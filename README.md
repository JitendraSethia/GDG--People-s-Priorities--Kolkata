# People's Priorities — Kolkata

**AI-powered civic grievance triage and constituency planning.** Citizens report issues in Bengali, Hindi, or English — by text, voice, or camera. Gemini classifies, translates, and summarizes every report; a transparent rule-based engine scores urgency; duplicate reports cluster into one issue; and officials get a live map, a triage dashboard, and a data-driven ward planning view.

Built for **Build with AI: Code for Communities**.

## What it does

**Citizen side** (web + native Android app):
- Report an issue in 4 steps: describe it (text or **voice input**, in bn/hi/en), snap a photo with the **native camera**, auto-detect location via **GPS → ward mapping** (no need to know ward numbers), submit.
- **Gemini classifies every report**: category, one-line English summary, translation, safety-risk and affected-count inference — with a deterministic rule-based fallback so submissions never fail.
- Track status by ticket ID, with a progress timeline and a **chatbot** that answers "why is this urgent?" from the real scoring reasons.
- "Recently fixed" page shows completed work — closing the trust loop.

**Authorities side** (`/officials`, passcode-gated):
- **Live Google Map** of active reports as urgency-colored pins + heatmap, updating in near-real-time.
- Triage dashboard: filterable queue sorted by urgency, one-tap status updates.
- **Explainable urgency**: every score expands into its reasons (severity baseline, risk keywords, people affected, days unresolved) — no black box.
- **Duplicate clustering**: geo + landmark + text-similarity matching folds N reports of the same pothole into one issue ("37 similar reports"), sized by citizens affected.
- **Ward planning view**: top issues per ward with 12-week trend direction — what to budget for, not just what to fix today.

## Architecture

- **Flask + SQLite** — application-factory, blueprints (`citizen`, `official`, `api`), no ORM.
- **Gemini API** (`google-genai`, `gemini-2.5-flash`) — structured JSON output with a response schema; 12s timeout; any failure falls back silently to rule-based classification. Urgency scoring is deliberately **rule-based and deterministic** (explainability by design); Gemini enriches, never overrides.
- **Google Maps JavaScript API** — officials' live map, markers + heatmap.
- **Capacitor** native Android wrapper — camera + geolocation via native plugins, pointed at the Flask server (`mobile/`).
- Citizen JS is **ES5-compatible** — verified on Android 9 WebView (Chrome 69).

## Quick start

```bash
python -m venv venv && venv/Scripts/activate   # or source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                            # add GEMINI_API_KEY + MAPS_API_KEY
python scripts/seed_db.py --reset               # ~330 realistic Kolkata reports, fixed seed
python app.py                                   # http://localhost:5000
```

- Citizen app: `http://localhost:5000`
- Officials console: `http://localhost:5000/officials` — default passcode `kolkata2026` (set `OFFICIAL_PASSCODE` in `.env`)
- Runs fully offline on rule-based fallbacks if no API keys are set.

Android app: `cd mobile && npm install && npx cap sync android && cd android && ./gradlew assembleDebug`. Point `server.url` in `mobile/capacitor.config.json` at your machine's LAN IP so the phone reaches Flask over WiFi.

## Demo

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the 5-step walkthrough: ward planning → duplicate cluster → explainable urgency → live Gemini submission → status chatbot.
