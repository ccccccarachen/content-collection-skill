import os
import re
import logging
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from notion_client import Client
import anthropic

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize clients
notion = Client(auth=NOTION_TOKEN)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# URL pattern
URL_PATTERN = re.compile(r'https?://[^\s]+')

# Noise patterns to remove from messages
NOISE_PATTERNS = [
    r'[,，]?\s*复制打开抖音.*$',
    r'[,，]?\s*复制此链接.*$',
    r'[,，]?\s*[Cc]opy and open Xiaohongshu.*$',
    r'[,，]?\s*打开抖音.*$',
    r'[,，]?\s*打开小红书.*$',
    r'[,，]?\s*点击链接.*$',
]


def extract_message_parts(message: str) -> tuple[str | None, str | None, bool]:
    """
    Extract title and URL from message.

    Returns:
        (title, url, needs_fetching)
        - If meaningful text exists before URL: (extracted_title, url, False)
        - If pure URL only: (None, url, True)
        - If no URL found: (None, None, False)
    """
    # Find URL in message
    url_match = URL_PATTERN.search(message)
    if not url_match:
        return None, None, False

    url = url_match.group()

    # Get text before URL
    text_before_url = message[:url_match.start()].strip()

    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        text_before_url = re.sub(pattern, '', text_before_url, flags=re.IGNORECASE).strip()

    # Check if there's meaningful text
    if text_before_url and len(text_before_url) > 2:
        return text_before_url, url, False
    else:
        return None, url, True


def fetch_url_content(url: str) -> str | None:
    """
    Fetch content from URL.
    Handles Twitter/X specially by extracting from meta tags.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to get og:description (works well for Twitter/X and many other sites)
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']

        # Try twitter:description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content']

        # Try regular meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']

        # Try og:title as fallback
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']

        # Try page title as last resort
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        return None

    except Exception as e:
        logger.error(f"Failed to fetch URL content: {e}")
        return None


def get_category_from_claude(title: str) -> str:
    """
    Use Claude to assign a category based on the title.
    """
    try:
        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on this title, assign a single category.
Categories should be in English, a single word or short phrase.
Common categories: Technology, Product, Career, Design, AI, Learning, Life, Finance, Health, Entertainment, Programming, Startup, Marketing, Psychology

Title: {title}

Respond with ONLY the category name, nothing else."""
                }
            ]
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.error(f"Failed to get category from Claude: {e}")
        return "Uncategorized"


def get_title_and_category_from_claude(content: str, url: str) -> tuple[str, str]:
    """
    Use Claude to create a title and assign a category based on fetched content.
    """
    try:
        # Truncate content if too long
        if len(content) > 2000:
            content = content[:2000] + "..."

        message = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on this content from a URL, provide:
1. A concise title (under 50 characters, match the source language - if content is Chinese, title should be Chinese)
2. A category in English (single word or short phrase)

Common categories: Technology, Product, Career, Design, AI, Learning, Life, Finance, Health, Entertainment, Programming, Startup, Marketing, Psychology

URL: {url}
Content: {content}

Respond in this exact format (two lines only):
TITLE: [your title here]
CATEGORY: [category here]"""
                }
            ]
        )

        response_text = message.content[0].text.strip()
        lines = response_text.split('\n')

        title = "Untitled"
        category = "Uncategorized"

        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("CATEGORY:"):
                category = line.replace("CATEGORY:", "").strip()

        return title, category

    except Exception as e:
        logger.error(f"Failed to get title and category from Claude: {e}")
        return "Untitled", "Uncategorized"


def save_to_notion(title: str, category: str, url: str) -> tuple[bool, str]:
    """Save entry to Notion database"""
    try:
        # Get current time in ISO 8601 format
        added_time = datetime.now(timezone.utc).isoformat()

        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Category": {
                    "select": {
                        "name": category
                    }
                },
                "Content": {
                    "rich_text": [
                        {
                            "text": {
                                "content": url
                            }
                        }
                    ]
                },
                "Added Time": {
                    "date": {
                        "start": added_time
                    }
                }
            }
        )
        return True, ""
    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")
        return False, str(e)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    text = update.message.text
    logger.info(f"Received message: {text[:100]}...")

    # Extract message parts
    title, url, needs_fetching = extract_message_parts(text)

    if not url:
        await update.message.reply_text(
            "❌ No URL found in message.\n"
            "Please send a message with a URL."
        )
        return

    # Send processing indicator
    await update.message.reply_text("⏳ Processing...")

    try:
        if needs_fetching:
            # TYPE B: Pure URL - need to fetch content and get both title and category
            logger.info(f"Type B: Pure URL detected, fetching content from {url}")
            content = fetch_url_content(url)

            if content:
                title, category = get_title_and_category_from_claude(content, url)
            else:
                # If we couldn't fetch content, use URL domain as hint
                title, category = get_title_and_category_from_claude(f"URL: {url}", url)
        else:
            # TYPE A: Has meaningful text - use it as title, just get category
            logger.info(f"Type A: Title detected: {title}")
            category = get_category_from_claude(title)

        # Save to Notion
        success, error = save_to_notion(title, category, url)

        if success:
            await update.message.reply_text(
                f"✅ Saved to Notion\n"
                f"Title: {title}\n"
                f"Category: {category}"
            )
        else:
            await update.message.reply_text(
                f"❌ Failed to save to Notion:\n{error}"
            )

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            f"❌ Error processing message:\n{str(e)}"
        )


def main() -> None:
    """Start the bot"""
    missing_vars = []

    if not TELEGRAM_BOT_TOKEN:
        missing_vars.append("TELEGRAM_BOT_TOKEN")
    if not NOTION_TOKEN:
        missing_vars.append("NOTION_TOKEN")
    if not NOTION_DATABASE_ID:
        missing_vars.append("NOTION_DATABASE_ID")
    if not ANTHROPIC_API_KEY:
        missing_vars.append("ANTHROPIC_API_KEY")

    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Bot started with AI-powered content summarization")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
