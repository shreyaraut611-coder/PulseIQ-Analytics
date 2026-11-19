# Going live: hosting choice (Task 17)

| Option | Free limits | Data size | Sleeping | Price | Runs Streamlit? | Runs FastAPI? |
|---|---|---|---|---|---|---|
| **Streamlit Community Cloud** | Public apps from a GitHub repo, ~1 GB memory per app | Files in the repo (keep well under 200 MB) | Sleeps after a period with no visitors; wakes on the next visit | Free | Yes | No |
| Hugging Face Spaces | 2 vCPU, 16 GB RAM (CPU basic) | Repo storage, large files via LFS | Sleeps after inactivity on free tier | Free; paid hardware optional | Yes | Yes (Docker) |
| Render (free web service) | 512 MB RAM | Repo files | Sleeps after ~15 min idle (slow first request) | Free; paid from a few dollars a month | Yes (Docker) | Yes |
| Self-hosted Metabase / Superset | Needs your own server and database | Unlimited | No | Server cost | No (different tool) | – |

*Limits change; check each platform's current page before relying on them.*

## My choice

**Dashboard → Streamlit Community Cloud.** It deploys straight from this GitHub repository, it is free, it
needs no Docker knowledge, and it redeploys automatically on every push. Our whole data folder is about
12 MB (7 MB of CSV tables + the 5 MB workbook) and the published aggregate layer is under 0.1 MB, far below
the limits. The app may sleep when nobody uses it; for a training project that is acceptable. For real users
I would pay for an always-on plan.

**API → Render free web service** (second service from the same repository, see `render.yaml`), because
Streamlit Community Cloud cannot run FastAPI.

## Settings and secrets

* No passwords or keys are needed for this data. The optional `PULSEIQ_TABLES` setting goes in the
  platform's **Secrets** box (format in `.streamlit/secrets.toml.example`), never in the code.
* `.streamlit/secrets.toml` and `.env` are in `.gitignore`.

## Data published

* Data files come from the repository (`data/tables`, `data/published`), never uploaded from a laptop.
* `scripts/export_published.py` creates the aggregate layer (`data/published/`) with a manifest of row counts,
  sizes and the cut-off. Pay is blanked for groups under 5 and attrition for groups under 10.
* If the platform limited us to 200 MB I would publish only the aggregate layer and the dimension tables, and
  leave out person-level facts (payroll, attendance, leave, tasks) and the original workbook.

## Scheduled refresh

`.github/workflows/refresh_data.yml` runs **every Monday at 05:30 IST**. It rebuilds the published layer, runs
the tests, and commits the result; Streamlit Cloud redeploys on that push. The page cache also expires every
24 hours (`st.cache_data(ttl=86400)`). The monthly PDF is built on the 2nd of each month at 06:00 IST
(`monthly_report.yml`).

## Stranger test

Ask someone who has never seen the app to open the link on their phone and find the September 2026 headcount.
Expected path: landing page → the "Headcount (Sep 2026)" tile (441), or the sidebar → 6 · Executive scorecard.
Write down how long it took and anything they got stuck on.
