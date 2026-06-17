# Automation Architecture

## The Requirement

The user should not need to upload files every day.

The website should update automatically as data changes, especially when lineups confirm.

## Important Reality

On free GitHub and free Vercel, fully guaranteed real-time automation is limited.

What is possible for free:

- Website auto-refreshes in the browser.
- GitHub Actions can run scheduled data refreshes.
- Vercel can serve the updated site/data.
- Serverless API routes can fetch data when a visitor opens the page.

What is not guaranteed for free:

- Precise every-minute cron execution.
- Always-on backend workers.
- Guaranteed schedule timing during busy GitHub windows.

## Recommended Product Architecture

### Phase 1: Free Reliable MVP

- Vercel hosts the Ghost Analytics website.
- A `/api/live-mlb` endpoint fetches or serves the newest slate data.
- GitHub Actions runs scheduled refreshes during MLB windows.
- Browser refreshes data every 60 seconds.
- Site shows stale-data warnings if data is old.
- Every run saves a timestamped snapshot.

### Phase 2: Better Live System

Use a lightweight database and scheduled worker:

- Supabase for storing slate snapshots and audit results.
- GitHub Actions or external scheduler for refresh jobs.
- Vercel frontend reads from Supabase.

### Phase 3: True Production

Use a dedicated worker/server:

- Always-on backend or scheduled worker.
- Queue-based refresh jobs.
- Database snapshots.
- Admin tools.
- User accounts/paywall.

## Data Freshness Rules

The site should display:

- Last refresh time in Eastern Time
- Data mode: Full Slate / Remaining Games / Confirmed Lineups / Projected
- Confirmed lineup count
- Stale warning if older than 10 minutes during active slate windows
- Error warning if latest refresh failed

