# Troubleshooting Guide

Common errors and solutions for the content-collection bot.

## Startup Errors

### "Missing environment variables: ..."

**Cause:** One or more required env vars not set.

**Fix:**
- Railway: Service > Variables tab. Ensure all 4 are set:
  - `TELEGRAM_BOT_TOKEN`
  - `NOTION_TOKEN`
  - `NOTION_DATABASE_ID`
  - `ANTHROPIC_API_KEY`
- Check for typos in variable names (case-sensitive)
- No quotes around values in Railway

### Bot crashes immediately / no "Bot started" log

**Cause:** Python dependency or import error.

**Fix:**
- Check Railway build logs for pip install errors
- Ensure `requirements.txt` is in repo root
- Verify `runtime.txt` specifies `python-3.12.3`

---

## Notion Errors

### 401 Unauthorized / "API token is invalid"

**Cause:** Notion integration token is wrong or expired.

**Fix:**
1. Go to https://www.notion.so/profile/integrations
2. Click your integration
3. Copy the token again (starts with `ntn_` or `secret_`)
4. Update in Railway Variables

### "Could not find database with ID: ..."

**Cause:** Database ID is wrong OR integration not connected to the database.

**Fix:**
1. Verify database ID: open database as full page, check URL
   - URL format: `https://www.notion.so/workspace/DATABASE_ID?v=VIEW_ID`
   - The ID is the 32-character hex string before `?v=`
2. Connect integration: database page > "..." menu > "Connections" > select your integration

### "Property Title is not a title" (or similar property errors)

**Cause:** Database columns don't match expected schema.

**Fix:** Ensure exact column structure:

| Column Name | Property Type |
|------------|---------------|
| Title | Title (default first column) |
| Category | Select |
| Added Time | Date |
| Content | Rich text |

- Column names are case-sensitive: "Added Time" not "added time"
- "Title" must be the title property (first column)
- "Category" must be Select (not Multi-select)
- "Content" must be Rich text (not Text or URL)

### "Validation error: select option not found"

**Cause:** Claude returned a category that doesn't exist as a Select option.

**Fix:**
- Open database > Category column header > edit options
- Ensure your desired categories are listed as Select options
- Categories are fetched dynamically - any change in Notion takes effect immediately

---

## Anthropic / Claude Errors

### "Could not validate credentials" / 401

**Cause:** Invalid Anthropic API key.

**Fix:**
1. Go to https://console.anthropic.com/settings/keys
2. Create a new key if needed
3. Key must start with `sk-ant-`
4. Update in Railway Variables

### "Rate limit exceeded" / 429

**Cause:** Too many API calls.

**Fix:**
- Wait a few minutes and retry
- Check Anthropic dashboard for usage limits
- Free tier has lower rate limits

### "Model not found"

**Cause:** The model ID in bot.py doesn't match available models.

**Fix:**
- The bot uses `claude-sonnet-4-20250514`
- Ensure your API key has access to this model
- Check https://docs.anthropic.com/en/docs/about-claude/models for current model IDs

---

## Telegram Errors

### Bot doesn't respond to messages

**Possible causes:**
1. **Bot not running:** Check Railway deployment status and logs
2. **Bot token wrong:** Verify with `https://api.telegram.org/bot<TOKEN>/getMe`
3. **Sending commands instead of text:** Bot only handles plain text, not `/commands`
4. **Sending to wrong bot:** Verify bot username matches @BotFather setup

### "Conflict: terminated by other getUpdates request"

**Cause:** Multiple instances of the bot running.

**Fix:**
- Ensure only ONE deployment is active in Railway
- If testing locally AND Railway is running, stop one
- Railway: remove extra services if duplicated

### Bot responds with "Processing..." but never completes

**Cause:** URL fetch timeout or API call hanging.

**Fix:**
- Check Railway logs for specific error
- URL may be unreachable (geo-blocked, requires auth, etc.)
- Anthropic API may be slow - check status at https://status.anthropic.com

---

## Railway Deployment Errors

### Build fails

**Common causes:**
- Missing `requirements.txt` in repo root
- Invalid `runtime.txt` syntax (must be exactly `python-3.12.3`)
- Network issues during pip install (retry deployment)

### Service keeps restarting

**Cause:** Bot crashes during startup.

**Fix:**
1. Check logs for the specific error
2. Most common: missing/invalid environment variables
3. Run `scripts/validate_setup.py` locally with your values

### "No start command found"

**Cause:** Railway can't find Procfile or it's malformed.

**Fix:**
- Ensure `Procfile` (capital P, no extension) is in repo root
- Contents must be exactly: `worker: python bot.py`
- No trailing whitespace or BOM characters

### Using too many Railway credits

**Cause:** Worker dyno runs 24/7.

**Fix:**
- Railway free tier: $5/month credit
- Bot uses minimal resources (idle most of the time)
- Monitor usage in Railway dashboard > Usage tab
- Consider upgrading if approaching limit

---

## Running Validation

Use the validation script to check everything at once:

```bash
# With environment variables set
python scripts/validate_setup.py

# With .env file
python scripts/validate_setup.py --env .env
```

The script checks:
- All 4 env vars present
- API key format validation
- Notion database connection and column structure
- Anthropic API connectivity
- Telegram bot token validity
