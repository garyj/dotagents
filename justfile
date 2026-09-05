default:
    just --list

# vendored skills: check | sync [--dry-run] [--latest] [NAME]; run `just skills --help` for the rest
skills *ARGS:
    uv run scripts/vendor_skill.py {{ ARGS }}

# link this checkout into every agent's config; --check reports without changing
install *ARGS:
    scripts/install {{ ARGS }}
