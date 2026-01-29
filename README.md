# Content Collection Bot

Save links and notes to Notion via Telegram. Send a URL or text, and the bot uses Claude AI to generate a title, pick a category, and save it to your Notion database.

## Features

- Send a URL — auto-generates a title and category, saves to Notion
- Send text + URL — uses your text as the title
- Send plain text — saves it as a note with AI-generated title
- Reply with a number — quickly change the category
- Special support for Twitter/X links

## Quick Start

1. **Start Claude Code:**
   ```
   claude
   ```

2. **Clone and open the project:**
   ```
   git clone https://github.com/ccccccarachen/content-collection-skill.git
   cd content-collection-skill
   ```

3. **Ask Claude to set up the bot:**
   ```
   Help me set up the content collection bot
   ```

Claude will walk you through everything:
- Getting your API keys (Anthropic, Notion, Telegram)
- Creating your Notion database with the right columns
- Deploying the bot to Railway
- Testing that it works

Just follow the prompts one at a time.

## How the Skill Works

This project includes a Claude Code **skill** — a file (`content-collection-setup/SKILL.md`) that teaches Claude how to guide you through setup interactively.

When you ask Claude for help inside this project folder, it automatically reads the skill and runs a step-by-step setup wizard: asks what you've done, validates your API keys, checks your Notion database, and troubleshoots errors.

## Getting API Keys

### Anthropic API

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Copy it (starts with `sk-ant-`)

### Notion Integration

1. Go to [notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. Create a new integration named "Content Collection Bot"
3. Copy the token (starts with `ntn_` or `secret_`)

### Telegram Bot

1. Open Telegram, message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the token (looks like `123456789:ABCdef...`)

### Railway (Hosting)

1. Sign up at [railway.com](https://railway.com) (GitHub login recommended)
2. Free trial includes $5 credit

## Notion Database Setup

Create a full-page database with these exact columns:

| Column | Type |
|--------|------|
| Title | Title |
| Category | Select |
| Added Time | Date |
| Content | Rich text |

Add your category options to the Select column (e.g. Article, Video, Tweet, Tutorial, Resource, Personal, Other).

Connect the integration: click **...** > **Connections** > select **Content Collection Bot**.

## Validate Your Setup

```
python scripts/validate_setup.py
```

This checks all API keys, connections, and database structure.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check Railway logs — deployment may have crashed |
| "Missing environment variables" | Check variable names in Railway Variables tab |
| Notion 401 error | Reconnect integration to database |
| Wrong categories | Category column must be Select type, not Multi-select |
| Content column empty | Column must be named exactly "Content" (Rich text) |

See `content-collection-setup/references/troubleshooting.md` for the full guide.

## Project Structure

```
├── bot.py                          # The bot (runs on Railway)
├── requirements.txt                # Python dependencies
├── Procfile                        # Railway start command
├── runtime.txt                     # Python version
└── content-collection-setup/       # Claude Code setup skill
    ├── SKILL.md                    # Skill instructions
    ├── assets/
    │   └── env.template            # Environment variable template
    ├── scripts/
    │   ├── validate_setup.py       # Setup validator
    │   └── create_railway_config.py# Railway config generator
    └── references/
        ├── notion_setup.md         # Notion setup details
        └── troubleshooting.md      # Full troubleshooting guide
```

## Cost

- **Anthropic API** — Pay-as-you-go, a few cents/month for casual use
- **Notion** — Free for personal use
- **Telegram** — Free
- **Railway** — $5 free trial credit, then ~$5/month

---

Built with Claude AI
