# People's Priorities — 5-Minute Demo Script

Lead with the intelligence, not the form. Rehearse this exact order.

## 1. Planning view (~45s) — establish the payoff first
Go to **Officials → Planning**, select **Salt Lake**.
> "Here's what Salt Lake actually needs this month — Streetlight complaints, 36 reports, and it's rising."

## 2. Duplicate cluster (~45s) — the workload-saving beat
Go to **Officials → Dashboard**, filter to Salt Lake.
Point at the "🔁 36 similar reports" chip on the streetlight item (PP-000011).
> "That's not 36 separate tickets an official has to triage one by one — it's one issue, 36 citizens affected. This is what most teams skip."

## 3. Urgency explainability (~30s)
Open **PP-000047** (Roads & Infrastructure, Jadavpur — score 75/high, status "acknowledged" so it reads as a live active case, not a closed one).
Click the urgency badge to expand the reasons.
> "Every score is explainable — baseline severity, risk keywords like 'accident', how many people it affects, how long it's been unresolved. Not a black box." (Narrative: a big pothole near Sulekha More caused an accident yesterday.)
>
> Fallback if a true critical item is wanted instead: PP-000006 (Electrical Hazard, New Town, score 85) — same explainability story, already resolved, so frame it as "here's the full lifecycle" rather than "this is still open."

## 4. Live submission (~90s) — the AI moment
Go to citizen **Report an Issue** (web or mobile app).
Submit in **Bengali or Hindi** if possible, or English.
> "Watch this get classified in real time." Switch to the dashboard — it should appear within one poll cycle (~5s).
Point out the category, summary, and urgency score Gemini assigned.

## 5. Status + chatbot (~30s) — close the loop
Go to citizen **Check Status**, enter the ticket ID just created.
Ask the chatbot "why is this urgent?" — show it answers from the real urgency reasons.

## Pre-demo checklist
- [ ] Flask running (`python app.py`), confirm `/api/meta` returns 200
- [ ] `.env` has `GEMINI_API_KEY` set — confirm a test submission's summary reads as a real translated/contextual sentence (Gemini), not raw echoed text (rule-based fallback)
- [ ] Fresh-looking data: re-seed if grievances look stale (`python scripts/seed_db.py --reset`) — the seed is pinned (`--seed 42` by default) so ticket IDs/wards referenced above (PP-000011, PP-000047, PP-000006) stay valid across re-seeds. Only the internal `cluster_id` strings change each run (UUID-based); the UI never shows those, so this doesn't matter.
- [ ] If you submit any test tickets after the last re-seed, re-seed once more right before presenting to clear them out — it's now safe to do without breaking the script above
- [ ] Close the Android emulator before the demo if not using it live — it competes for RAM with Flask on this machine (7.9GB total RAM)
- [ ] If demoing mobile: `adb reverse tcp:5000 tcp:5000` re-run after any reconnect, app already installed
