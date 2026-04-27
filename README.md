# Client Interaction Management System (CIMS)

A fully self-contained, single-file web app for managing client accounts, logging sales calls, and tracking team performance.

---

## Quick Start

Just open `index.html` in any modern browser — no install, no server, no build step required.

```
double-click index.html
```

---

## Features

| Feature | Details |
|---|---|
| Account management | Add, search, sort, import via CSV |
| Call logging | Date, team member, status, notes, custom fields |
| Dashboard | Coverage rate, branch metrics, urgency list |
| Activity chart | 8 chart types · Daily / Weekly / Monthly / Yearly |
| Role system | Admin, Manager, Rep, Viewer with permission matrix |
| Rep view | Reps only see their own performance data |
| Field Builder | Add custom fields to Accounts, Users, Calls (Admin only) |
| Call statuses | Configurable dropdown (Completed, No Answer, etc.) |
| CSV import | Bulk add or update accounts from a spreadsheet |
| Dark mode | Automatic, follows OS preference |

---

## Deployment Options

### Option A — Open locally (zero setup)
Double-click `index.html`. Works offline, no internet after first load.

### Option B — Netlify Drop (free, 30 seconds)
1. Go to [netlify.com/drop](https://netlify.com/drop)
2. Drag the `index.html` file onto the page
3. Get a live public URL instantly

### Option C — GitHub Pages (free, permanent)
1. Create a new GitHub repository
2. Upload `index.html` as the only file
3. Go to Settings → Pages → Deploy from branch `main`
4. Your app is live at `https://yourusername.github.io/repo-name`

### Option D — SharePoint (Microsoft 365)
1. Upload `index.html` to a SharePoint document library
2. On any SharePoint page, add an **Embed** web part
3. Paste the file URL — the app renders inline

### Option E — Any web server
Copy `index.html` to any folder served by Apache, Nginx, IIS, or an S3 static bucket. No configuration needed.

---

## Upgrading to a Full React App (optional)

To add persistent storage or a real backend, convert to a Vite project:

```bash
npm create vite@latest cims -- --template react
cd cims
npm install
# Paste the JS logic from index.html into src/App.jsx
npm run dev
```

For a database, consider **Supabase** (free tier, Postgres) or **Firebase Realtime Database**.

---

## CSV Import Format

Download the template from inside the app, or use this column order:

```
Account ID, Account Name, Brand Name, # of Branches, Sector, Contact Person
```

- `Account ID` is optional for new rows (auto-generated if blank)
- Use **Update existing** mode to overwrite accounts by matching ID

---

## Default Users & Roles

| Name | Role | Can log calls | Can add accounts | Can manage users | Can edit fields |
|---|---|---|---|---|---|
| Ahmed Al-Harbi | Admin | ✓ | ✓ | ✓ | ✓ |
| Sara Al-Zahrani | Manager | ✓ | ✓ | — | — |
| Mohammed Al-Ghamdi | Rep | ✓ | — | — | — |
| Fatima Al-Otaibi | Rep | ✓ | — | — | — |
| Khalid Al-Qahtani | Viewer | — | — | — | — |

Switch active user from the chip in the top-right corner to preview any role.

---

## Notes

- All data is in-memory and resets on page refresh. For persistence, integrate with localStorage or a backend API.
- The app loads React, Chart.js, and PapaParse from CDN — requires internet on first load.
- Dark mode is automatic based on your OS setting.
