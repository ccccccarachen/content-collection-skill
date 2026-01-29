#!/usr/bin/env python3
"""
Generate Railway environment variable configuration.

Outputs environment variables in formats suitable for:
1. Railway CLI bulk import
2. Copy-paste into Railway dashboard
3. Local .env file for testing

Usage:
    python create_railway_config.py                          # Interactive prompt
    python create_railway_config.py --env .env --format cli  # From existing .env
"""

import os
import re
import sys
import json


REQUIRED_VARS = [
    {
        "name": "TELEGRAM_BOT_TOKEN",
        "prompt": "Telegram bot token (from @BotFather)",
        "pattern": r"^\d+:[A-Za-z0-9_-]{35,}$",
        "hint": "Format: 123456789:ABCdefGHI...",
    },
    {
        "name": "NOTION_TOKEN",
        "prompt": "Notion integration token",
        "pattern": r"^(ntn_|secret_)",
        "hint": 'Starts with "ntn_" or "secret_"',
    },
    {
        "name": "NOTION_DATABASE_ID",
        "prompt": "Notion database ID (32 hex chars or URL)",
        "pattern": r"[a-f0-9]{32}",
        "hint": "32 hex characters from database URL",
    },
    {
        "name": "ANTHROPIC_API_KEY",
        "prompt": "Anthropic API key",
        "pattern": r"^sk-ant-",
        "hint": 'Starts with "sk-ant-"',
    },
]


def extract_database_id(raw: str) -> str | None:
    """Extract 32-char hex database ID from URL or raw string."""
    cleaned = raw.replace("-", "").strip()
    match = re.search(r"([a-f0-9]{32})", cleaned)
    if match:
        db_id = match.group(1)
        return f"{db_id[:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}"
    return None


def load_env_file(path: str) -> dict[str, str]:
    """Load key=value pairs from .env file."""
    values = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def collect_interactive() -> dict[str, str]:
    """Interactively collect all required values."""
    print("\nEnter your configuration values:")
    print("(Press Ctrl+C to cancel)\n")

    values = {}
    for var in REQUIRED_VARS:
        while True:
            value = input(f"  {var['prompt']}\n  [{var['hint']}]: ").strip()

            if not value:
                print(f"  Required. {var['hint']}\n")
                continue

            # Special handling for database ID (accept URLs)
            if var["name"] == "NOTION_DATABASE_ID":
                extracted = extract_database_id(value)
                if extracted:
                    value = extracted
                    print(f"  Extracted ID: {value}")
                else:
                    print(f"  Could not extract database ID. {var['hint']}\n")
                    continue
            elif not re.search(var["pattern"], value):
                print(f"  Invalid format. {var['hint']}\n")
                continue

            values[var["name"]] = value
            print()
            break

    return values


def format_env(values: dict[str, str]) -> str:
    """Format as .env file."""
    lines = ["# Content Collection Bot - Environment Variables", ""]
    for var in REQUIRED_VARS:
        name = var["name"]
        if name in values:
            lines.append(f"{name}={values[name]}")
    return "\n".join(lines) + "\n"


def format_cli(values: dict[str, str]) -> str:
    """Format as Railway CLI commands."""
    lines = ["# Run these commands in your Railway project directory:", ""]
    for var in REQUIRED_VARS:
        name = var["name"]
        if name in values:
            lines.append(f'railway variables set {name}="{values[name]}"')
    return "\n".join(lines) + "\n"


def format_dashboard(values: dict[str, str]) -> str:
    """Format for copy-paste into Railway dashboard."""
    lines = [
        "# Add these in Railway > Service > Variables tab:",
        "# Click 'RAW Editor' and paste the following:",
        "",
    ]
    for var in REQUIRED_VARS:
        name = var["name"]
        if name in values:
            lines.append(f"{name}={values[name]}")
    return "\n".join(lines) + "\n"


def format_json(values: dict[str, str]) -> str:
    """Format as JSON (for Railway API or programmatic use)."""
    ordered = {}
    for var in REQUIRED_VARS:
        name = var["name"]
        if name in values:
            ordered[name] = values[name]
    return json.dumps(ordered, indent=2) + "\n"


FORMATTERS = {
    "env": ("Local .env file", format_env),
    "cli": ("Railway CLI commands", format_cli),
    "dashboard": ("Railway dashboard (RAW Editor)", format_dashboard),
    "json": ("JSON", format_json),
}


def main() -> None:
    print("=" * 50)
    print("  Railway Configuration Generator")
    print("=" * 50)

    # Parse args
    env_path = None
    output_format = "env"
    output_file = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--env" and i + 1 < len(args):
            env_path = args[i + 1]
            i += 2
        elif args[i] == "--format" and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif args[i] == "--help":
            print(__doc__)
            print("Formats: " + ", ".join(FORMATTERS.keys()))
            sys.exit(0)
        else:
            i += 1

    # Collect values
    if env_path:
        if not os.path.exists(env_path):
            print(f"ERROR: File not found: {env_path}")
            sys.exit(1)
        values = load_env_file(env_path)
        print(f"\nLoaded {len(values)} variables from {env_path}")
    else:
        try:
            values = collect_interactive()
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            sys.exit(0)

    # Validate we have all vars
    missing = [v["name"] for v in REQUIRED_VARS if v["name"] not in values]
    if missing:
        print(f"\nWARNING: Missing variables: {', '.join(missing)}")

    # Format output
    if output_format not in FORMATTERS:
        print(f"Unknown format: {output_format}")
        print("Available: " + ", ".join(FORMATTERS.keys()))
        sys.exit(1)

    label, formatter = FORMATTERS[output_format]
    result = formatter(values)

    print(f"\n--- {label} ---\n")
    print(result)

    # Optionally write to file
    if output_file:
        with open(output_file, "w") as f:
            f.write(result)
        print(f"Written to: {output_file}")

    # Also offer to generate .env for local testing
    if output_format != "env" and not output_file:
        print("Tip: Add --format env --output .env to save a local .env file for testing.")


if __name__ == "__main__":
    main()
