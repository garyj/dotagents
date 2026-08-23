# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "rich>=13", "typer>=0.12"]
# ///
"""Sync vendored third-party skills in home/dot_agents/skills/ from upstream.

Each vendored skill carries a .provenance naming its upstream repo, the subpath
the skill lives at, the pinned commit, and the vetting verdict. This script
re-copies that subpath at the pinned commit, so `sync NAME` is an idempotent
drift check and `sync NAME --latest` is the update.

Vendored content is byte-identical to upstream by design, which keeps every
future comparison a cmp rather than a merge. Nothing here merges: sync
overwrites, and prunes files upstream no longer ships.

The pinned commit is the repo revision the content was taken from, not the last
revision to touch the skill, so "behind" always means the skill's own bytes
changed. Unrelated upstream traffic never raises a false alarm.
"""

from __future__ import annotations

import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

SKILLS_DIR = Path("home/dot_agents/skills")
PROVENANCE = "dot_provenance"

app = typer.Typer(help=__doc__, no_args_is_help=True, add_completion=False)
console = Console()


def fail(message: str) -> typer.Exit:
    console.print(message, style="red")
    return typer.Exit(1)


def gh(*args: str) -> bytes:
    result = subprocess.run(["gh", *args], capture_output=True, check=False)
    if result.returncode != 0:
        raise fail(f"gh {' '.join(args)} failed: {result.stderr.decode().strip()}")
    return result.stdout


def gh_json(endpoint: str) -> Any:
    return json.loads(gh("api", endpoint))


def load_skills(names: list[str]) -> dict[str, dict[str, str]]:
    """Read .provenance for the named skills, or every vendored skill."""
    skills = {}
    for provenance in sorted(SKILLS_DIR.glob(f"*/{PROVENANCE}")):
        name = provenance.parent.name
        if names and name not in names:
            continue
        data = yaml.safe_load(provenance.read_text())
        for field in ("source", "path", "commit"):
            if field not in data:
                raise fail(f"{provenance}: missing required field '{field}'")
        skills[name] = data
    missing = set(names) - set(skills)
    if missing:
        raise fail(f"not vendored (no {PROVENANCE}): {', '.join(sorted(missing))}")
    if not skills:
        raise fail(f"no vendored skills found under {SKILLS_DIR}")
    return skills


def repo_slug(source: str) -> str:
    return source.removeprefix("https://github.com/").removesuffix(".git")


def default_head(slug: str) -> tuple[str, str]:
    """Head of the upstream default branch, as (sha, date)."""
    branch = gh_json(f"/repos/{slug}")["default_branch"]
    commit = gh_json(f"/repos/{slug}/commits/{branch}")
    return commit["sha"], commit["commit"]["committer"]["date"][:10]


def fetch_subtree(slug: str, sha: str, path: str, into: Path) -> Path:
    """Extract the repo tarball at sha and return the requested subpath."""
    archive = into / "upstream.tar.gz"
    archive.write_bytes(gh("api", f"/repos/{slug}/tarball/{sha}"))
    with tarfile.open(archive) as tar:
        root = tar.getnames()[0].split("/")[0]
        tar.extractall(into, filter="tar")
    subtree = into / root / path
    if not subtree.exists():
        raise fail(f"{slug}@{sha[:7]}: {path} does not exist")
    return subtree


def source_name(entry: Path) -> str:
    """Encode a target file's attributes into a chezmoi source filename."""
    name = entry.name
    if name.startswith("."):
        name = f"dot_{name.removeprefix('.')}"
    if entry.is_symlink():
        return f"symlink_{name}"
    if entry.stat().st_mode & 0o100:
        return f"executable_{name}"
    return name


def build_plan(subtree: Path, dest: Path) -> dict[Path, bytes]:
    """Map each destination path to the bytes it should hold."""
    if subtree.is_file():
        return {dest / source_name(subtree): subtree.read_bytes()}

    plan = {}
    for entry in sorted(subtree.rglob("*")):
        if entry.is_dir() and not entry.is_symlink():
            continue
        target = dest / entry.relative_to(subtree).parent / source_name(entry)
        # chezmoi stores a symlink as a file holding its target path.
        link = entry.readlink().name if entry.is_symlink() else None
        plan[target] = f"{link}\n".encode() if link else entry.read_bytes()
    return plan


def plan_sync(name: str, data: dict[str, str], sha: str, tmp: Path) -> tuple[dict[Path, bytes], set[Path]]:
    """Work needed to make the skill directory match upstream at sha."""
    subtree = fetch_subtree(repo_slug(data["source"]), sha, data["path"], tmp)
    dest = SKILLS_DIR / name
    plan = build_plan(subtree, dest)
    writes = {p: c for p, c in plan.items() if not p.exists() or p.read_bytes() != c}
    prunes = {p for p in dest.rglob("*") if p.is_file() and p.name != PROVENANCE} - set(plan)
    return writes, prunes


def write_provenance(path: Path, data: dict[str, str]) -> None:
    order = ["source", "path", "commit", "vetted"]
    keys = order + [k for k in data if k not in order]
    path.write_text("\n".join(f"{k}: {data[k]}" for k in keys if k in data) + "\n")


def require_repo_root() -> None:
    if not SKILLS_DIR.is_dir():
        raise fail(f"run from the repo root: {SKILLS_DIR} not found")


Names = Annotated[list[str] | None, typer.Argument(help="Skills to act on (default: all).")]


@app.command()
def check(names: Names = None) -> None:
    """Report which vendored skills changed upstream."""
    require_repo_root()
    table = Table(box=None, pad_edge=False)
    for column in ("skill", "status", "pinned", "upstream", "date"):
        table.add_column(column)

    for name, data in load_skills(names or []).items():
        head, when = default_head(repo_slug(data["source"]))
        changed = 0
        if head != data["commit"]:
            with tempfile.TemporaryDirectory() as tmp:
                writes, prunes = plan_sync(name, data, head, Path(tmp))
                changed = len(writes) + len(prunes)
        table.add_row(
            name,
            f"behind ({changed} files)" if changed else "up to date",
            data["commit"][:7],
            head[:7] if changed else "",
            when if changed else "",
            style="yellow" if changed else "green",
        )
    console.print(table)


@app.command()
def sync(
    names: Names = None,
    latest: Annotated[
        bool, typer.Option(help="Move to the upstream default branch head.")
    ] = False,
    dry_run: Annotated[bool, typer.Option(help="Report what would change, write nothing.")] = False,
) -> None:
    """Copy upstream content into the skill directory.

    With no flags this re-copies the pinned commit, so it both heals and detects
    drift. A dry run that finds drift at the pinned commit exits non-zero.
    """
    require_repo_root()
    drifted = False

    for name, data in load_skills(names or []).items():
        slug = repo_slug(data["source"])
        sha = data["commit"]
        if latest:
            sha, when = default_head(slug)
            if sha == data["commit"]:
                console.print(f"{name}: already at {slug}@{sha[:7]}")
                continue
            console.print(f"{name}: {data['commit'][:7]} -> {sha[:7]} ({when})", style="bold")

        with tempfile.TemporaryDirectory() as tmp:
            writes, prunes = plan_sync(name, data, sha, Path(tmp))
            for path in sorted(writes):
                verb, style = ("update", "yellow") if path.exists() else ("add", "green")
                console.print(f"  {verb:>6}  {path}", style=style)
            for path in sorted(prunes):
                console.print(f"  {'prune':>6}  {path}", style="red")
            if not writes and not prunes:
                console.print(f"{name}: matches {slug}@{sha[:7]}", style="green")
            drifted = drifted or bool(writes or prunes)

            if dry_run:
                continue
            for path, content in writes.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            for path in prunes:
                path.unlink()

        if latest:
            data["commit"] = sha
            if writes or prunes:
                # The content is new, so the old verdict no longer describes it.
                data["vetted"] = f"PENDING - previous: {data['vetted']}"
            write_provenance(SKILLS_DIR / name / PROVENANCE, data)

    if drifted and dry_run and not latest:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
