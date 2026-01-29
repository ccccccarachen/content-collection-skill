# Notion Database Setup Guide

Detailed instructions for creating and configuring the Notion database used by the content-collection bot.

## Step 1: Create a Notion Integration

1. Go to **https://www.notion.so/profile/integrations**
2. Click **"New integration"**
3. Configure:
   - **Name:** Content Collection Bot
   - **Associated workspace:** Select your workspace
   - **Type:** Internal
4. Click **Submit**
5. Copy the **"Internal Integration Secret"**
   - Starts with `ntn_` (newer) or `secret_` (older)
   - Save this — it's your `NOTION_TOKEN`

### Integration Capabilities (defaults are fine)

- Content Capabilities: Read, Update, Insert — all needed
- No user capabilities needed
- No comment capabilities needed

---

## Step 2: Create the Database

### Option A: Create from Scratch

1. Open Notion
2. Create a new page (or navigate to where you want the database)
3. Type `/database` and select **"Database - Full page"**
4. Name it whatever you like (e.g., "Content Collection")

### Option B: Quick Setup

1. Create a new page
2. Type `/table` and select **"Table - Full page"**
3. This creates a database with a default "Name" title column

---

## Step 3: Configure Columns

You need exactly these 4 columns with these exact names and types:

### Column 1: Title (title type)

- This is the default first column in any Notion database
- If you used Option B, rename "Name" to **"Title"**
- Click the column header > "Rename" > type "Title"
- Type is automatically "Title" (cannot be changed for first column)

### Column 2: Category (select type)

1. Click **"+"** to add a new column
2. Name it exactly: **Category**
3. Set type to: **Select**
4. Add your category options:
   - Click the column header > "Edit property"
   - Under "Options", add each category
   - Suggested categories: **Article, Video, Tweet, Tutorial, Resource, Personal, Other**
   - Choose colors for each (optional but helpful for visual scanning)

**Important:** The bot reads categories directly from this Select property. To change available categories later, just edit the Select options here — the bot picks up changes automatically.

### Column 3: Added Time (date type)

1. Click **"+"** to add a new column
2. Name it exactly: **Added Time**
3. Set type to: **Date**
4. No additional configuration needed

### Column 4: Content (rich text type)

1. Click **"+"** to add a new column
2. Name it exactly: **Content**
3. Set type to: **Text** (this creates a rich_text property)
4. No additional configuration needed

### Final Database Layout

```
| Title (title)     | Category (select) | Added Time (date) | Content (rich text) |
|-------------------|-------------------|--------------------|---------------------|
| Example Article   | Article           | 2025-01-15         | https://example.com |
```

---

## Step 4: Connect Integration to Database

**This step is required** — without it, the bot cannot access the database.

1. Open your database as a **full page**
2. Click the **"..."** menu (top right corner)
3. Click **"Connections"** (or "Add connections")
4. Search for **"Content Collection Bot"** (your integration name)
5. Click to connect
6. Confirm when prompted

If you don't see your integration:
- Check it was created in the same workspace
- Try refreshing the page
- Go back to https://www.notion.so/profile/integrations and verify it exists

---

## Step 5: Get the Database ID

1. Open your database as a **full page** (not as an inline view)
2. Look at the browser URL:
   ```
   https://www.notion.so/your-workspace/DATABASE_ID?v=VIEW_ID
   ```
3. The **DATABASE_ID** is the 32-character hexadecimal string
   - Example URL: `https://www.notion.so/myspace/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4?v=...`
   - Database ID: `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4`
4. The ID may or may not have hyphens — both formats work

**Alternative method:**
- Click "Share" on the database page
- Click "Copy link"
- Extract the ID from the copied URL

---

## Verification Checklist

Before proceeding to deployment, verify:

- [ ] Integration created and token copied
- [ ] Database has exactly 4 columns: Title, Category, Added Time, Content
- [ ] Column types are correct: title, select, date, rich_text
- [ ] Category Select options are added (at least one)
- [ ] Integration is connected to the database
- [ ] Database ID extracted from URL

---

## Common Mistakes

| Mistake | How to Fix |
|---------|-----------|
| "Name" instead of "Title" for first column | Click column header > Rename to "Title" |
| Multi-select instead of Select for Category | Delete column, recreate as Select |
| "Text" shows as wrong type | Ensure it says "Text" in column config (maps to rich_text in API) |
| Column names with wrong capitalization | Exact match required: "Added Time" not "added time" |
| Integration not connected | "..." menu > Connections > add your integration |
| Database is inline (not full page) | Click "Open as full page" or create a new full-page database |
| Copied view ID instead of database ID | Database ID comes BEFORE `?v=` in the URL |
