# Bus Tracker Project (Flask + SQLite + Bootstrap 5 + Chart.js)

## Next Action
1. **Current State:** Mobile-first dashboard redesign complete. Replaced broken Chart.js box-and-whisker plots and wide desktop tables with Today's Hero Gauges (Style C), a Weekly Schedule toggle (`Range Track` vs. `Dot Strip`), and a modern `Trend & Drift Analysis` section (`Weekly Curve` with 5th–95th confidence band + Last-10 drift line vs. `Date History` rolling average) with automatic Wednesday early-dismissal scaling.
2. **Next Target:** Deploy updated templates and `app.py` to the production `docker` host (`/home/mb/bus-tracker`) and validate with live current-year bus data.
3. **First Command:** `docker compose restart web`

## Native CLI Commands
- **Run Tests (uv):** `.venv/bin/pytest`
- **Setup Local Env (uv):** `uv venv && uv pip install -r requirements.txt pytest`
- **Run Local Dev Server:** `.venv/bin/python app.py` (serves on `http://localhost:5000`)
- **Restart Docker Container (Bind-Mounted Code/Templates):** `docker compose restart web`
- **Rebuild & Restart Docker Container:** `docker compose up --build -d`
- **Check Container Status:** `docker compose ps`

## Context & Constraints
- **Stack:** Python 3.12, Flask, Pandas, SQLite (`database.db`), Bootstrap 5, Chart.js, Docker + Gunicorn (`port 5000`).
- **Architecture:**
  - `app.py`: All routes, PIN verification (`ENTRY_PIN` in `.env`), SQLite initialization (`init_db()`), and Pandas statistical aggregation (`/api/summary-data`, `/api/entries`, `/api/submit`, `/api/update-data`, `/api/delete-data`).
  - `templates/base.html` & `templates/summary.html`: Mobile-first UI, dark/light theme toggle, bottom-sheet modals, horizontal timeline gauges, and Chart.js trend curves.
  - `database.db`: Ignored by git (`.gitignore`). Local file holds sample/historical data; live production database lives on the `docker` host at `/home/mb/bus-tracker` persisted via volume mount in `docker-compose.yml`.
- **Wednesday Early Dismissal Quirk:** School dismisses ~1.5 hours early on Wednesdays (~2:40 PM vs. ~4:00 PM). Afternoon timelines and trend charts must isolate or normalize Wednesday so Monday/Tuesday/Thursday/Friday scales are never squished.
- **Rules for Gemini:**
  - Propose a max 3-step plan before writing code.
  - Keep diffs small and limited to the current step.
  - Always restart or rebuild the Docker container (`docker compose restart web` or `docker compose up --build -d`) after editing Python or template files so changes take effect on port 5000.
  - Maintain mobile responsiveness on all UI edits (compact padding on `<576px`, valid Bootstrap 5 spacing classes only, no horizontal table overflow, touch-friendly controls).
  - When told to log a side-quest, append it to `## Backlog` below and return immediately to the active step.

## Backlog
- [x] Fix mobile scaling where components/divs are too large and do not scale on phones. (Resolved: compact header, visible mobile theme toggle, responsive cards)
- [x] Replace broken vertical box-and-whisker plots with horizontal timeline gauges (`Range Track` + `Dot Strip` toggle) and separate Wednesday early-dismissal scaling. (Resolved)
- [x] Modernize Morning/Afternoon trend charts with `Weekly Curve` (5th–95th band + Last-10 drift) and `Date History` (40-trip scatter + 5-trip rolling average) toggle. (Resolved)
- [x] Fix current-day highlight row padding where `Fri` and window numbers sat too close to the highlight border. (Resolved: `px-2` + transparent inner track)
- [x] Update `test_app.py` school-year filter test (`test_api_summary_filtering`) to use a dynamic current-school-year date instead of hardcoded `2026-05-05`. (Resolved)
