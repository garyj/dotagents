default:
    just --list

# vendored skills: check | sync [--dry-run] [--latest] [NAME]; run `just skills --help` for the rest
skills *ARGS:
    uv run scripts/vendor_skill.py {{ ARGS }}

# gh-installed skills in .claude/skills: update all to upstream; --dry-run reports without changing
gh-skills *ARGS:
    gh skill update --all --dir .claude/skills {{ ARGS }}

# link this checkout into every agent's config; --check reports without changing
install *ARGS:
    scripts/install {{ ARGS }}
