---
name: rapidapi-studio-listing
description: >
  Step-by-step workflow for listing and configuring an API on RapidAPI Hub using
  RapidAPI Studio. Covers project creation, endpoint definitions, hub listing
  details, gateway configuration, monetization tiers, and best practices learned
  from hands-on browser automation (June 2026).
---

# RapidAPI Studio — API Listing Workflow

## Overview
This skill documents the complete workflow for listing an API on RapidAPI Hub,
based on direct exploration and successful browser automation of the RapidAPI
Studio interface (June 2026). Includes detailed UI navigation for browser agents.

## Reference Screenshots
See `resources/` directory for UI reference screenshots:
- `monetize_plan_dialog.png` — The plan settings dialog (Plan Type, Rate Limit, Price)
- `monetize_quota_dialog.png` — The quota/requests dialog (Quota Type, Quota Limit, Limit Type)

## RapidAPI Studio Structure

### Left Sidebar Tabs
1. **Requests** — API client for testing endpoints (like Postman). Organized into groups/folders
2. **Tests** — Automated test configurations
3. **Hub Listing** — The main configuration area (see sub-tabs below)
4. **Analytics** — Usage metrics and monitoring
5. **Settings** — Transfer ownership, delete project. NOTE: API project name CANNOT be renamed from this page.

### Hub Listing Sub-Tabs (Top Navigation Bar)
1. **General** — Logo, Category, Short/Long Description, Website, Visibility toggle
2. **Definitions** — Endpoint management with groups. Sub-tabs: Endpoints, Security, CI/CD
3. **Docs** — Additional documentation pages
4. **Gateway** — Base URL, RapidAPI proxy secret, IP whitelisting
5. **Community** — Discussion/community settings
6. **Monetize** — Pricing plans and quotas

## Step-by-Step Listing Process

### Step 1: Create API Project
1. Navigate to `https://rapidapi.com/studio`
2. Click **"Add API Project"** button (top area of Studio dashboard)
3. A dialog appears with fields for:
   - **API Name** (text input)
   - **API Description** (text area) — short description
   - Optional: **Import from** toggle — can import from OpenAPI URL
4. If importing from OpenAPI: toggle "Import from" ON, paste the OpenAPI spec URL
   (e.g., `https://your-api.onrender.com/openapi.json`)
5. Click **"Create"** or **"Add API"** button at bottom of dialog

### Step 2: Configure Hub Listing > General
1. Click **"Hub Listing"** in left sidebar → click **"General"** tab (top nav)
2. Fill in:
   - **Logo**: Click the logo upload area → select 500x500px PNG/JPEG file
   - **Category**: Select from dropdown (e.g., "Tools", "Data")
   - **Short Description**: Plain text shown on marketplace card (~100 chars)
   - **Long Description**: Markdown text for the listing page (endpoint list, use cases)
   - **Website**: URL to documentation or landing page
3. Scroll down → Click **"Save"** button
4. **Visibility toggle**: Found at bottom of General tab or in a separate section
   - Check **"I confirm I own or have rights to publish"** checkbox
   - Toggle **"Switch Visibility"** to ON for PUBLIC
   - Save

### Step 3: Configure Definitions > Endpoints
1. Click **"Definitions"** tab (top nav)
2. To import endpoints: Click **"CI/CD"** sub-tab → look for import option
   - Paste OpenAPI spec URL: `https://your-api.onrender.com/openapi.json`
   - Click import/sync
3. Endpoints appear organized into groups based on OpenAPI tags
4. To manually organize: Use "Create Group" and "Create Endpoint" buttons
5. Each endpoint needs: Name, Method, Path, Description, Parameters

### Step 4: Configure Gateway
1. Click **"Gateway"** tab (top nav)
2. **Base URL section**: Set to your deployed API URL
   (e.g., `https://your-api.onrender.com`)
3. The **X-RapidAPI-Proxy-Secret** is displayed on this page — copy it!
   - This MUST be added to your backend as an environment variable
   - Your FastAPI middleware validates this header to ensure requests come through RapidAPI
4. Optionally enable: IP whitelisting, injection protection, request size limits
5. Click **"Save"**

### Step 5: Configure Monetization (DETAILED UI NAVIGATION)

> **CRITICAL**: This section has two separate dialog types per plan. The browser
> agent MUST handle both correctly.

#### 5a. Navigate to Monetize Tab
1. Click **"Monetize"** tab (top nav)
2. You'll see the **"Public Plans"** sub-tab selected by default
3. The page shows plan columns: **BASIC**, **PRO**, **ULTRA**, **MEGA**
4. Each plan has:
   - A toggle switch (ON/OFF) at the top to enable/disable the plan
   - The plan name and price below the toggle
   - An **"Edit"** button (blue, full-width)
   - Below that: **Objects** section with "Requests" and "Bandwidth Platform Fee"
   - A **"+"** button next to each object to add quota for that plan

#### 5b. Enable Plans
- **BASIC** is always enabled (free tier, cannot be disabled)
- Toggle ON the plans you want: **PRO**, **ULTRA**, **MEGA**
- Click the toggle switch next to each plan name

#### 5c. Set Plan Prices — Click the "Edit" Button
1. Click the **"Edit"** button under a plan name (e.g., PRO)
2. A dialog opens titled with the plan name (e.g., "BASIC" or "PRO")
3. Dialog fields:
   - **Plan Type**: Radio buttons — "Monthly Subscription" (default), "Pay per Use", "Tiers"
   - **Rate Limit**: Checkbox (optional rate limiting)
   - **Require approval**: Checkbox (consumers need approval to subscribe)
   - **Recommended Plan**: Checkbox (adds "Recommended" badge — only one plan at a time)
   - **Subscription Price**: Text input field showing `$ 0` — TYPE THE PRICE HERE
4. Set the **Subscription Price** (e.g., `9.99` for PRO, `29.99` for ULTRA, `99.99` for MEGA)
5. Click **"Save Changes"** button at bottom right

> **Browser Agent Note**: The price input is a standard text field with `$ ` prefix.
> Clear the field first, then type the numeric price. Use `fill` tool, NOT
> JavaScript manipulation. The dialog has Cancel and Save Changes buttons at bottom.

#### 5d. Set Request Quotas — Click the "+" or Quota Link
1. Under **Objects** section, find **"Requests"** row
2. Click the **"+"** button or existing quota link next to the plan column
3. A dialog opens titled **"{PLAN_NAME} / Requests"**
4. Dialog fields:
   - **Quota Type**: Radio buttons — "Unlimited", "Monthly" (select Monthly), "Daily"
   - **Quota Limit**: Text input — enter the number (e.g., `1500`, `30000`, `300000`, `1500000`)
   - **Limit Type**: Radio buttons — "Soft Limit" (allows overage fees), "Hard Limit" (blocks requests)
   - Select **"Hard Limit"** for most cases
5. Click **"Save Changes"**

> **WARNING**: RapidAPI defaults the BASIC (free) plan to 500,000 requests/month.
> This is far too generous — always explicitly set the BASIC plan quota to 1,500/month
> (or your intended free tier limit). Do NOT skip quota configuration on the free tier.

> **Browser Agent Note**: The quota dialog is a SEPARATE dialog from the price dialog.
> You must click in a different place to access it. The "+" button is in the Objects
> section under each plan column, NOT the "Edit" button which opens the price dialog.

#### 5e. Standard Pricing Templates

**For Consumer/Professional APIs** (e.g., electrical calculators):
| Plan | Price | Requests/mo | Limit Type |
|------|-------|-------------|------------|
| BASIC | $0 | 1,500 | Hard |
| PRO | $9.99 | 30,000 | Hard |
| ULTRA | $29.99 | 300,000 | Hard |
| MEGA | $99.99 | 1,500,000 | Hard |

**For Enterprise/Utility APIs** (e.g., reliability indices):
| Plan | Price | Requests/mo | Limit Type |
|------|-------|-------------|------------|
| BASIC | $0 | 1,500 | Hard |
| PRO | $29.99 | 30,000 | Hard |
| ULTRA | $99.99 | 300,000 | Hard |
| MEGA | $299.99 | 1,500,000 | Hard |

**For Niche/Specialty APIs** (e.g., fire protection):
| Plan | Price | Requests/mo | Limit Type |
|------|-------|-------------|------------|
| BASIC | $0 | 1,500 | Hard |
| PRO | $19.99 | 30,000 | Hard |
| ULTRA | $49.99 | 300,000 | Hard |

### Step 6: Upload Logo
1. Go to **General** tab
2. Click the logo upload area (shows default octopus icon or current logo)
3. Use browser file upload to select the PNG file
4. Save after upload

### Step 7: Go Public
1. Go to **General** tab, scroll to visibility section
2. Check **"I confirm I own or have rights to publish"** checkbox
3. Toggle **"Switch Visibility"** to ON
4. Save — API is now PUBLIC on the marketplace

## Multi-Listing Strategy (Split by Module)

When an API has multiple distinct buyer personas, split into separate RapidAPI
listings. Each listing is a separate "API Project" in Studio.

### Benefits
- 3x marketplace discovery (separate search results)
- Targeted descriptions per buyer persona
- Independent pricing per audience budget
- Higher total revenue if buyer needs multiple modules

### How to Split
1. One FastAPI backend serves all modules at different path prefixes
   (e.g., `/v1/electrical`, `/v1/fire`, `/v1/utility`)
2. Create separate RapidAPI projects, each pointing to the SAME Render URL
3. Each project imports all endpoints but descriptions focus on its module
4. Set different pricing per audience:
   - High-demand consumer → lower price, higher volume
   - Enterprise/niche → higher price, lower competition

## Key Learnings
- Always include a generous free tier (BASIC) — it's the primary discovery mechanism
- RapidAPI takes ~25% marketplace fee on paid plans
- The proxy secret header validation prevents direct API access bypass
- Short Description is the most critical text — shown on the marketplace card
- API project names CANNOT be renamed after creation (only descriptions can change)
- The Monetize "Edit" button opens the PLAN dialog (price), NOT the quota dialog
- The "+" button in the Objects section opens the QUOTA dialog (request limits)
- These are TWO SEPARATE dialogs — browser agents must handle both
- Bandwidth Platform Fee defaults to $0.001/MB and is usually left as-is
- The API preview card shows: Popularity score, Latency, Success Rate
- **OpenAPI import via CI/CD resets the General tab** — always configure General tab AFTER importing endpoints, not before
- When splitting into multiple listings, do imports first, then fill descriptions
- Plan pricing may need manual verification after browser automation — always screenshot the final state
