# Client Interaction Management System — Python / Streamlit

A fully self-contained Streamlit app for managing client accounts, logging sales calls, and tracking team performance.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

---

## Features

| Feature | Details |
|---|---|
| Account management | Add, search, sort, import via CSV |
| Call logging | Date, team member, status, notes, custom fields |
| Dashboard | Coverage rate, branch metrics, urgency list |
| Activity chart | 7 chart types · Daily / Weekly / Monthly / Yearly · pagination |
| Role system | Admin, Manager, Rep, Viewer with permission matrix |
| Rep view | Reps only see their own performance data |
| Field Builder | Custom fields for Accounts, Users, Calls (Admin only) |
| Call statuses | Configurable with color picker |
| CSV import | Bulk add or update accounts |
| Export | Download activity log as CSV |
| Dark mode | Automatic, follows OS/browser preference |

---

## Deployment Options

### Option A — Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Option B — Streamlit Community Cloud (free, permanent URL)
1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and select `app.py`
4. Click Deploy — live in ~60 seconds

### Option C — Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
```bash
docker build -t cims .
docker run -p 8501:8501 cims
```

### Option D — Azure / AWS / GCP
Deploy the Docker container to any cloud container service:
- **Azure Container Apps** — `az containerapp up`
- **AWS App Runner** — push to ECR, deploy
- **Google Cloud Run** — `gcloud run deploy`

---

## CSV Import Format

```
Account ID, Account Name, Brand Name, # of Branches, Sector, Contact Person
```

- `Account ID` is optional for new rows (auto-generated if blank)
- Use **Update existing** mode to overwrite accounts by matching ID

---

## Default Users

| Name | Role |
|---|---|
| Ahmed Al-Harbi | Admin |
| Sara Al-Zahrani | Manager |
| Mohammed Al-Ghamdi | Rep |
| Fatima Al-Otaibi | Rep |
| Khalid Al-Qahtani | Viewer |

Switch the active user from the sidebar to preview any role.

---

## Adding Persistent Storage

Data is currently in-memory (resets on restart). To persist data, replace the `st.session_state` account/user lists with calls to a database:

```python
# Example: SQLite (local)
import sqlite3
conn = sqlite3.connect("cims.db", check_same_thread=False)

# Example: Supabase (cloud Postgres, free tier)
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```
