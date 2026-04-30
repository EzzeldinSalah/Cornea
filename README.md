# Cornea

Financial intelligence tool for Arab freelancers. Think of it as "git for your income" -- it tracks invoices, exchange rates, and gives you an AI coach that actually reads your numbers before talking.

## Architecture

```
cornea/
  api/                    # Python backend (FastAPI)
    main.py               # All API routes
    database.py           # SQLite operations (snapshots, users, settings)
    coach.py              # LangChain + Gemini AI coach logic
    prompts.py            # Dynamic system prompt builder (tone + language)
    currency_exchange_api.py  # Live exchange rate fetcher
    requirements.txt      # Python dependencies
  src/                    # Frontend (SvelteKit)
    routes/
      +page.svelte        # Landing page
      auth/+page.svelte   # Login / signup (email + Google)
      (app)/
        +layout.svelte    # Dashboard shell (sidebar + content area)
        log/              # Financial history timeline
        diff/             # Month-over-month comparison
        blame/            # Per-client breakdown
        coach/            # AI chat interface
        settings/         # User preferences
  .env                    # Environment variables (not committed)
  vite.config.ts          # Vite dev server + API proxy
```

### How it works

The frontend is a SvelteKit app. The backend is a FastAPI server. In development, Vite proxies all `/api/*` requests to the FastAPI server running on port 8000.

The database is a single SQLite file (`cornea.db`) created automatically on first startup. It stores financial snapshots, user accounts (bcrypt-hashed passwords), user settings, and coach chat sessions.

The AI coach uses Google Gemini via LangChain. It reads the user's financial data and responds based on their chosen tone (blunt / balanced / gentle) and language (English / Arabic / mixed).

## Environment variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-google-gemini-api-key
CURRENCY_EXCHANGE_API_URL=https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json
PUBLIC_GOOGLE_CLIENT_ID=your-google-oauth-client-id
JWT_SECRET=any-random-string-for-signing-tokens
```

`PUBLIC_GOOGLE_CLIENT_ID` uses the `PUBLIC_` prefix so SvelteKit exposes it to the browser (needed for the Google sign-in button). All other variables stay server-side only.

## Setup

### Backend

```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
# from the project root
pnpm install
```

Open `http://localhost:5173` in your browser. The Vite dev server proxies API calls to `localhost:8000` automatically.

On first visit, go to the Log page and click "Run Mock Sync" to populate the database with sample data.

## Database

SQLite file at `api/cornea.db`. Tables:

| Table                 | Purpose                                                              |
| --------------------- | -------------------------------------------------------------------- |
| `snapshots`         | Financial history entries (invoices, fees, rates)                    |
| `monthly_summaries` | Aggregated monthly data                                              |
| `coach_sessions`    | Chat session titles                                                  |
| `message_store`     | Chat message history (created by LangChain)                          |
| `users`             | Accounts (email, bcrypt password hash, Google ID)                    |
| `user_settings`     | Per-user preferences (language, currency, coach tone, notifications, and avatar BLOBs) |

To reset everything, stop the server and delete `cornea.db`. It will be recreated on next startup.

**>** Built at SalamHack 2026 by Team Cornea.
