#!/usr/bin/env python3
"""
Validate content-collection bot setup.

Checks all environment variables, API key formats, and service connections.
Run after setting up .env or Railway environment variables.

Usage:
    python validate_setup.py              # Uses environment variables
    python validate_setup.py --env .env   # Loads from .env file
"""

import os
import re
import sys
import json

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env_file(path: str) -> None:
    """Load key=value pairs from a .env file into os.environ."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    symbol = "+" if passed else "!"
    msg = f"  [{symbol}] {label}: {status}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_env_vars() -> dict[str, str | None]:
    """Check that all required env vars exist and return their values."""
    print("\n== Environment Variables ==")
    required = [
        "TELEGRAM_BOT_TOKEN",
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID",
        "ANTHROPIC_API_KEY",
    ]
    values = {}
    for var in required:
        val = os.environ.get(var)
        values[var] = val
        check(var, val is not None, "set" if val else "missing")
    return values


def validate_formats(values: dict[str, str | None]) -> dict[str, bool]:
    """Validate API key / token formats."""
    print("\n== Format Validation ==")
    results = {}

    # Anthropic
    key = values.get("ANTHROPIC_API_KEY") or ""
    ok = bool(re.match(r"^sk-ant-", key))
    check("Anthropic API key format", ok, 'should start with "sk-ant-"')
    results["anthropic_format"] = ok

    # Notion token
    token = values.get("NOTION_TOKEN") or ""
    ok = token.startswith("ntn_") or token.startswith("secret_")
    check("Notion token format", ok, 'should start with "ntn_" or "secret_"')
    results["notion_format"] = ok

    # Notion database ID (32 hex chars, with or without hyphens)
    db_id = values.get("NOTION_DATABASE_ID") or ""
    cleaned = db_id.replace("-", "")
    ok = bool(re.fullmatch(r"[a-f0-9]{32}", cleaned))
    check("Notion database ID format", ok, "should be 32 hex characters")
    results["db_id_format"] = ok

    # Telegram token
    tg = values.get("TELEGRAM_BOT_TOKEN") or ""
    ok = bool(re.match(r"^\d+:[A-Za-z0-9_-]{35,}$", tg))
    check("Telegram bot token format", ok, 'should match "NUMBER:ALPHANUMERIC"')
    results["telegram_format"] = ok

    return results


def test_notion_connection(values: dict[str, str | None]) -> bool:
    """Test Notion API connection and database structure."""
    print("\n== Notion Connection ==")
    token = values.get("NOTION_TOKEN")
    db_id = values.get("NOTION_DATABASE_ID")

    if not token or not db_id:
        check("Notion connection", False, "missing token or database ID")
        return False

    try:
        from notion_client import Client

        notion = Client(auth=token)

        # Test: retrieve database
        db = notion.databases.retrieve(database_id=db_id)
        check("Notion database access", True, f'"{db.get("title", [{}])[0].get("plain_text", "Untitled")}"')

        # Validate columns
        props = db.get("properties", {})
        expected = {
            "Title": "title",
            "Category": "select",
            "Added Time": "date",
            "Content": "rich_text",
        }
        all_ok = True
        for col_name, col_type in expected.items():
            prop = props.get(col_name)
            if prop is None:
                check(f'Column "{col_name}"', False, "missing")
                all_ok = False
            elif prop.get("type") != col_type:
                check(f'Column "{col_name}"', False, f'expected type "{col_type}", got "{prop.get("type")}"')
                all_ok = False
            else:
                detail = f"type={col_type}"
                if col_type == "select":
                    options = prop.get("select", {}).get("options", [])
                    names = [o["name"] for o in options]
                    detail += f", options={names}"
                check(f'Column "{col_name}"', True, detail)

        return all_ok

    except ImportError:
        check("Notion connection", False, 'notion-client not installed - run "pip install notion-client"')
        return False
    except Exception as e:
        check("Notion connection", False, str(e))
        return False


def test_anthropic_connection(values: dict[str, str | None]) -> bool:
    """Test Anthropic API connection with a minimal request."""
    print("\n== Anthropic Connection ==")
    api_key = values.get("ANTHROPIC_API_KEY")

    if not api_key:
        check("Anthropic connection", False, "missing API key")
        return False

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'ok'"}],
        )
        text = response.content[0].text.strip()
        check("Anthropic API call", True, f"response: {text}")
        return True

    except ImportError:
        check("Anthropic connection", False, 'anthropic not installed - run "pip install anthropic"')
        return False
    except Exception as e:
        check("Anthropic connection", False, str(e))
        return False


def test_telegram_token(values: dict[str, str | None]) -> bool:
    """Test Telegram bot token by calling getMe."""
    print("\n== Telegram Connection ==")
    token = values.get("TELEGRAM_BOT_TOKEN")

    if not token:
        check("Telegram connection", False, "missing token")
        return False

    try:
        import requests

        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        data = resp.json()
        if data.get("ok"):
            bot_info = data["result"]
            check(
                "Telegram bot",
                True,
                f'@{bot_info.get("username", "?")} ({bot_info.get("first_name", "?")})',
            )
            return True
        else:
            check("Telegram bot", False, data.get("description", "unknown error"))
            return False

    except ImportError:
        check("Telegram connection", False, 'requests not installed - run "pip install requests"')
        return False
    except Exception as e:
        check("Telegram connection", False, str(e))
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 50)
    print("  Content Collection Bot - Setup Validator")
    print("=" * 50)

    # Optionally load .env
    if "--env" in sys.argv:
        idx = sys.argv.index("--env")
        if idx + 1 < len(sys.argv):
            env_path = sys.argv[idx + 1]
            if os.path.exists(env_path):
                load_env_file(env_path)
                print(f"\nLoaded environment from: {env_path}")
            else:
                print(f"\nERROR: File not found: {env_path}")
                sys.exit(1)

    # 1. Check env vars
    values = validate_env_vars()
    all_present = all(v is not None for v in values.values())

    # 2. Validate formats
    formats = validate_formats(values)

    # 3. Test connections (only if formats pass)
    notion_ok = False
    anthropic_ok = False
    telegram_ok = False

    if all_present:
        if formats.get("notion_format") and formats.get("db_id_format"):
            notion_ok = test_notion_connection(values)
        else:
            print("\n== Notion Connection ==")
            check("Notion connection", False, "skipped due to format errors")

        if formats.get("anthropic_format"):
            anthropic_ok = test_anthropic_connection(values)
        else:
            print("\n== Anthropic Connection ==")
            check("Anthropic connection", False, "skipped due to format errors")

        if formats.get("telegram_format"):
            telegram_ok = test_telegram_token(values)
        else:
            print("\n== Telegram Connection ==")
            check("Telegram connection", False, "skipped due to format errors")
    else:
        print("\nSkipping connection tests - not all env vars present.")

    # Summary
    print("\n" + "=" * 50)
    print("  Summary")
    print("=" * 50)

    total = 0
    passed = 0
    checks = [
        ("Environment variables", all_present),
        ("Format validation", all(formats.values())),
        ("Notion connection", notion_ok),
        ("Anthropic connection", anthropic_ok),
        ("Telegram connection", telegram_ok),
    ]
    for label, ok in checks:
        total += 1
        if ok:
            passed += 1
        symbol = "+" if ok else "!"
        print(f"  [{symbol}] {label}: {'PASS' if ok else 'FAIL'}")

    print(f"\n  Result: {passed}/{total} checks passed")

    if passed == total:
        print("\n  Your bot is ready to deploy!")
    else:
        print("\n  Fix the failing checks above before deploying.")
        print("  See references/troubleshooting.md for help.")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
