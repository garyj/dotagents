# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13", "typer>=0.12"]
# ///
"""Sync vendored third-party skills in skills/ from upstream.

Each vendored skill carries a .provenance.json naming its upstream repo, the
subpath the skill lives at, the pinned commit, and a vetting log. This script
re-copies that subpath at the pinned commit, so `sync NAME` is an idempotent
drift check and `sync NAME --latest` is the update.

Vendored content is upstream bytes plus the patches in the skill's .patches/
directory, applied in name order. Nothing here merges: sync overwrites, and
prunes files upstream no longer ships. A hand edit is drift until
`patch NAME SLUG --why ...` captures it as a patch.

The pinned commit is the repo revision the content was taken from, not the last
revision to touch the skill, so "behind" always means the skill's own bytes
changed. Unrelated upstream traffic never raises a false alarm.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Annotated, Any, NamedTuple

import typer
from rich.console import Console
from rich.table import Table

SKILLS_DIR = Path("skills")
PROVENANCE = ".provenance.json"
PATCHES_DIR = ".patches"

app = typer.Typer(help=__doc__, no_args_is_help=True, add_completion=False)
console = Console()


class Entry(NamedTuple):
    """A file as it should exist on disk. For a symlink, data is the target."""

    data: bytes
    symlink: bool
    executable: bool


class Plan(NamedTuple):
    """What a skill directory should hold, and how the directory differs from it."""

    entries: dict[Path, Entry]
    writes: dict[Path, Entry]
    prunes: set[Path]
    failed_patches: list[Path]


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


def load_skills(names: list[str]) -> dict[str, dict[str, Any]]:
    """Read the provenance of the named skills, or of every vendored skill."""
    skills = {}
    for provenance in sorted(SKILLS_DIR.glob(f"*/{PROVENANCE}")):
        name = provenance.parent.name
        if names and name not in names:
            continue
        data = json.loads(provenance.read_text())
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


def write_provenance(name: str, data: dict[str, Any]) -> None:
    order = ["source", "path", "commit", "vetted"]
    ordered = {k: data[k] for k in order if k in data} | {k: v for k, v in data.items() if k not in order}
    (SKILLS_DIR / name / PROVENANCE).write_text(json.dumps(ordered, indent=2) + "\n")


def repo_slug(source: str) -> str:
    return source.removeprefix("https://github.com/").removesuffix(".git")


def default_head(slug: str) -> tuple[str, str]:
    """Head of the upstream default branch, as (sha, date)."""
    branch = gh_json(f"/repos/{slug}")["default_branch"]
    commit = gh_json(f"/repos/{slug}/commits/{branch}")
    return commit["sha"], commit["commit"]["committer"]["date"][:10]


def fetch_subtree(slug: str, sha: str, path: str, into: Path) -> Path:
    """Extract the repo tarball at sha and return the requested subpath as a directory."""
    archive = into / "upstream.tar.gz"
    archive.write_bytes(gh("api", f"/repos/{slug}/tarball/{sha}"))
    with tarfile.open(archive) as tar:
        root = tar.getnames()[0].split("/")[0]
        tar.extractall(into, filter="tar")
    subtree = into / root / path
    if not subtree.exists():
        raise fail(f"{slug}@{sha[:7]}: {path} does not exist")
    if subtree.is_file():
        single = into / "single"
        single.mkdir()
        shutil.copy2(subtree, single / subtree.name, follow_symlinks=False)
        return single
    return subtree


def apply_patches(name: str, subtree: Path) -> list[Path]:
    """Apply the skill's patches to the fetched subtree; return the ones that did not apply."""
    failed = []
    for patch in sorted((SKILLS_DIR / name / PATCHES_DIR).glob("*.patch")):
        result = subprocess.run(
            ["git", "apply", str(patch.resolve())], cwd=subtree, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            console.print(f"  {'failed':>6}  {patch}: {result.stderr.strip()}", style="red")
            failed.append(patch)
    return failed


def present(path: Path) -> bool:
    """True for a dangling symlink too, which Path.exists() reports as missing."""
    return path.is_symlink() or path.exists()


def read_entry(path: Path) -> Entry:
    if path.is_symlink():
        return Entry(str(path.readlink()).encode(), True, False)
    return Entry(path.read_bytes(), False, bool(path.stat().st_mode & 0o100))


def write_entry(path: Path, entry: Entry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if present(path):
        path.unlink()
    if entry.symlink:
        path.symlink_to(entry.data.decode())
        return
    path.write_bytes(entry.data)
    path.chmod(0o755 if entry.executable else 0o644)


def upstream_files(dest: Path) -> set[Path]:
    """Files in the skill directory that upstream owns: everything but the provenance and patches."""
    return {
        p
        for p in dest.rglob("*")
        if (p.is_symlink() or p.is_file()) and p.name != PROVENANCE and PATCHES_DIR not in p.relative_to(dest).parts
    }


def plan_sync(name: str, data: dict[str, Any], sha: str, tmp: Path) -> Plan:
    subtree = fetch_subtree(repo_slug(data["source"]), sha, data["path"], tmp)
    failed = apply_patches(name, subtree)
    dest = SKILLS_DIR / name
    entries = {}
    for entry in sorted(subtree.rglob("*")):
        if entry.is_dir() and not entry.is_symlink():
            continue
        entries[dest / entry.relative_to(subtree)] = read_entry(entry)
    writes = {p: e for p, e in entries.items() if not present(p) or read_entry(p) != e}
    prunes = upstream_files(dest) - set(entries)
    return Plan(entries, writes, prunes, failed)


def require_repo_root() -> None:
    if not SKILLS_DIR.is_dir():
        raise fail(f"run from the repo root: {SKILLS_DIR} not found")


Names = Annotated[list[str] | None, typer.Argument(help="Skills to act on (default: all).")]


@app.command()
def check(
    names: Names = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print one JSON object per skill instead of a table.")] = False,
) -> None:
    """Report which vendored skills changed upstream."""
    require_repo_root()
    rows = []
    for name, data in load_skills(names or []).items():
        head, when = default_head(repo_slug(data["source"]))
        changed, conflicts = 0, 0
        if head != data["commit"]:
            with tempfile.TemporaryDirectory() as tmp:
                plan = plan_sync(name, data, head, Path(tmp))
                changed = len(plan.writes) + len(plan.prunes)
                conflicts = len(plan.failed_patches)
        rows.append(
            {
                "skill": name,
                "behind": bool(changed),
                "pinned": data["commit"],
                "upstream": head,
                "date": when,
                "changed_files": changed,
                "patch_conflicts": conflicts,
            }
        )

    if as_json:
        print(json.dumps(rows, indent=2))
        return
    table = Table(box=None, pad_edge=False)
    for column in ("skill", "status", "pinned", "upstream", "date"):
        table.add_column(column)
    for row in rows:
        status = "up to date"
        if row["behind"]:
            status = f"behind ({row['changed_files']} files"
            status += f", {row['patch_conflicts']} patch conflicts)" if row["patch_conflicts"] else ")"
        table.add_row(
            row["skill"],
            status,
            row["pinned"][:7],
            row["upstream"][:7] if row["behind"] else "",
            row["date"] if row["behind"] else "",
            style="yellow" if row["behind"] else "green",
        )
    console.print(table)


@app.command()
def sync(
    names: Names = None,
    latest: Annotated[bool, typer.Option(help="Move to the upstream default branch head.")] = False,
    dry_run: Annotated[bool, typer.Option(help="Report what would change, write nothing.")] = False,
) -> None:
    """Copy upstream content plus the skill's patches into the skill directory.

    With no flags this re-copies the pinned commit, so it both heals and detects
    drift. A dry run that finds drift at the pinned commit exits non-zero. With
    --latest, a patch that no longer applies is reported, left in place, and
    noted in the vetting log; the exit status is non-zero so a caller notices.
    """
    require_repo_root()
    drifted = conflicted = False

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
            plan = plan_sync(name, data, sha, Path(tmp))
            if plan.failed_patches and not latest:
                raise fail(f"{name}: a patch does not apply at the pinned commit; fix or delete it")
            for path in sorted(plan.writes):
                verb, style = ("update", "yellow") if present(path) else ("add", "green")
                console.print(f"  {verb:>6}  {path}", style=style)
            for path in sorted(plan.prunes):
                console.print(f"  {'prune':>6}  {path}", style="red")
            if not plan.writes and not plan.prunes:
                console.print(f"{name}: matches {slug}@{sha[:7]}", style="green")
            drifted = drifted or bool(plan.writes or plan.prunes)
            conflicted = conflicted or bool(plan.failed_patches)

            if dry_run:
                continue
            for path, entry in plan.writes.items():
                write_entry(path, entry)
            for path in plan.prunes:
                path.unlink()

        if latest and not dry_run:
            if plan.writes or plan.prunes or plan.failed_patches:
                note = f"{dt.datetime.now(tz=dt.UTC).date()} PENDING: bumped {data['commit'][:7]} -> {sha[:7]}"
                if plan.failed_patches:
                    note += ", patches not applied: " + ", ".join(p.name for p in plan.failed_patches)
                data["vetted"] = [*data.get("vetted", []), note]
            data["commit"] = sha
            write_provenance(name, data)

    if (drifted and dry_run and not latest) or conflicted:
        raise typer.Exit(1)


@app.command()
def patch(
    name: Annotated[str, typer.Argument(help="Vendored skill whose hand edits to capture.")],
    slug: Annotated[str, typer.Argument(help="Short name for the patch file.")],
    why: Annotated[str, typer.Option(help="One line on why the change exists; becomes the patch header.")],
) -> None:
    """Capture the hand edits in a skill directory as its next patch file."""
    require_repo_root()
    data = load_skills([name])[name]
    dest = SKILLS_DIR / name
    with tempfile.TemporaryDirectory() as tmp:
        plan = plan_sync(name, data, data["commit"], Path(tmp))
        if plan.failed_patches:
            raise fail(f"{name}: an existing patch does not apply; fix that first")
        if not plan.writes and not plan.prunes:
            raise fail(f"{name}: no hand edits to capture")
        expected, actual = Path(tmp) / "a", Path(tmp) / "b"
        for path, entry in plan.entries.items():
            write_entry(expected / path.relative_to(dest), entry)
        for path in upstream_files(dest):
            write_entry(actual / path.relative_to(dest), read_entry(path))
        diff = subprocess.run(
            ["git", "-c", "diff.noprefix=false", "diff", "--no-index", "--no-prefix", "a", "b"], cwd=tmp, capture_output=True, text=True, check=False
        ).stdout

    patches = dest / PATCHES_DIR
    patches.mkdir(exist_ok=True)
    target = patches / f"{len(list(patches.glob('*.patch'))) + 1:03d}-{slug}.patch"
    target.write_text(f"{why.strip()}\n\n{diff}")
    console.print(f"wrote {target}", style="green")


if __name__ == "__main__":
    app()
