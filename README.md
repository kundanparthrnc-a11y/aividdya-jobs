# aividdya-jobs

Automated job feed for **aividdya.com/jobs**. A GitHub Actions workflow runs
`fetch_jobs.py` every morning, pulls AI/Data jobs from free job APIs, and
commits `jobs.json`. The website loads it via jsDelivr CDN:

```
https://cdn.jsdelivr.net/gh/kundanparthrnc-a11y/aividdya-jobs@main/jobs.json
```

## Setup — API keys (one time)

Add these under **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Where to get it (free) |
|---|---|
| `JSEARCH_API_KEY` | rapidapi.com → sign up → subscribe to **JSearch (OpenWeb Ninja)** → **Basic $0/mo** → copy `x-rapidapi-key` |
| `ADZUNA_APP_ID` | developer.adzuna.com → register app |
| `ADZUNA_APP_KEY` | Same page as above |

Then run once manually: **Actions → "Fetch AI/Data jobs" → Run workflow**.
