---
name: rapidapi-studio-listing
description: Step-by-step workflow for listing and configuring an API on RapidAPI Hub using RapidAPI Studio. Covers project creation, endpoint definitions, hub listing details, gateway configuration, monetization tiers, and best practices learned from hands-on exploration.
---

# RapidAPI Studio — API Listing Workflow

## Overview
This skill documents the complete workflow for listing an API on RapidAPI Hub, based on direct exploration of the RapidAPI Studio interface (June 2026).

## RapidAPI Studio Structure

### Left Sidebar Tabs
1. **Requests** — API client for testing endpoints (like Postman). Organized into groups/folders
2. **Tests** — Automated test configurations
3. **Hub Listing** — The main configuration area (see sub-tabs below)
4. **Analytics** — Usage metrics and monitoring
5. **Settings** — Transfer ownership, delete project

### Hub Listing Sub-Tabs
1. **General** — Logo (500x500 JPEG/PNG), Category, Short Description (plain text for API card), Long Description (markdown, appears on listing page), Website URL, Terms of Use
2. **Definitions** — Endpoint management with groups, methods, and actions (Create Endpoint, Create Group, Copy, Edit, Move). Sub-tabs: Endpoints, Security, CI/CD
3. **Docs** — Additional documentation pages
4. **Gateway** — Base URL, RapidAPI proxy secret (X-RapidAPI-Proxy-Secret), IP whitelisting, SQL/JS injection protection, request schema validation, request size limits
5. **Community** — Discussion/community settings
6. **Monetize** — 4 plan tiers (BASIC/PRO/ULTRA/MEGA) with per-plan quotas. Objects: Requests (per month), Bandwidth (per MB with overage pricing). Features section for plan differentiation. Tabs: Public Plans, Private Plans, Transactions

## Step-by-Step Listing Process

### Step 1: Create API Project
- Go to RapidAPI Studio → "Add API Project"
- Name it descriptively (e.g., "TradesCalc Electrical API")
- Import OpenAPI spec if available (from FastAPI's `/openapi.json`)

### Step 2: Configure Hub Listing > General
- Upload professional logo (500x500px)
- Set Category (e.g., "Tools", "Data")
- Write compelling Short Description (shown on API card in marketplace)
- Write detailed Long Description with markdown (use cases, code examples, endpoint summary)
- Add website URL (e.g., tradescalc.dev)

### Step 3: Configure Definitions > Endpoints
- Organize endpoints into Groups (e.g., "Electrical", "Utility", "Fire")
- Each endpoint needs: Name, Method, Path, Description, Parameters
- Use "Create Group" and "Create Endpoint" buttons
- CI/CD sub-tab can auto-sync from OpenAPI spec

### Step 4: Configure Gateway
- Set base URL to your deployed API (e.g., Render URL)
- Copy the X-RapidAPI-Proxy-Secret and add to your backend env vars
- Optionally enable IP whitelisting, injection protection

### Step 5: Configure Monetization
- Enable pricing tiers (BASIC is always on and free)
- Set request quotas per tier per month
- Set bandwidth limits and overage fees
- Add features to differentiate tiers

### Step 6: Publish
- Visibility defaults to PRIVATE — switch to PUBLIC when ready
- Version is set to v1 by default

## Key Learnings
- Always include a generous free tier (BASIC) — it's the primary developer discovery mechanism
- RapidAPI takes ~25% marketplace fee on paid plans
- The proxy secret header validation prevents direct access bypass
- Bandwidth has a platform fee ($0.001/MB overage by default)
- Short Description is the most important text for marketplace discovery (shown on card)
- The API preview card shows: Popularity score, Latency, Success Rate
