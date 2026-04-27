"""
Client Interaction Management System (CIMS)
A Streamlit application for managing client accounts and tracking team call activity.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import random
import io
import json

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Client Interaction Management",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }
    .metric-container { background: #f7f7f5; border-radius: 10px; padding: 14px 18px; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 6px 14px; }
    .badge-success { background:#EAF3DE; color:#27500A; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .badge-warn    { background:#FAEEDA; color:#633806; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .badge-danger  { background:#FCEBEB; color:#791F1F; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .badge-info    { background:#E6F1FB; color:#0C447C; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .role-admin   { background:#EEEDFE; color:#3C3489; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .role-manager { background:#E1F5EE; color:#085041; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .role-rep     { background:#FAEEDA; color:#633806; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    .role-viewer  { background:#F1EFE8; color:#444441; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:500; }
    div[data-testid="stMetricValue"] > div { font-size: 1.6rem !important; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .rep-banner { background:#E6F1FB; color:#0C447C; padding:10px 14px; border-radius:8px; margin-bottom:1rem; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ───────────────────────────────────────────────────────────────────
ROLES = {
    "admin":   {"label": "Admin",   "perms": {"view","log","add_account","import","manage_users","export","manage_schema"}},
    "manager": {"label": "Manager", "perms": {"view","log","add_account","import","export"}},
    "rep":     {"label": "Rep",     "perms": {"view","log"}},
    "viewer":  {"label": "Viewer",  "perms": {"view"}},
}
ROLE_PERMS_LABELS = [
    ("view",          "View accounts"),
    ("log",           "Log calls"),
    ("add_account",   "Add accounts"),
    ("import",        "Import CSV"),
    ("manage_users",  "Manage users"),
    ("export",        "Export data"),
    ("manage_schema", "Manage fields"),
]
TEAM_COLORS = [
    {"color": "#185FA5", "bg": "#E6F1FB"},
    {"color": "#0F6E56", "bg": "#E1F5EE"},
    {"color": "#993C1D", "bg": "#FAECE7"},
    {"color": "#993556", "bg": "#FBEAF0"},
    {"color": "#854F0B", "bg": "#FAEEDA"},
    {"color": "#534AB7", "bg": "#EEEDFE"},
]
SECTORS = ["Retail","F&B","Finance","Healthcare","Logistics","Tech","Education","Real Estate"]
BRANDS = [
    ("Al Futtaim Group","ACE Hardware"),("Alshaya Group","Starbucks ME"),
    ("Majid Al Futtaim","Mall of the Emirates"),("Jarir Bookstore","Jarir"),
    ("Extra Stores","Extra"),("Nahdi Medical","Nahdi"),("Tamimi Markets","Tamimi"),
    ("Abdul Latif Jameel","ALJ Auto"),("Gulf Union Foods","Sunbulah"),("Sadafco","Saudia Dairy"),
    ("National Water Company","NWC"),("Saudi Airlines Catering","SAC"),
    ("Binzagr Company","Binzagr"),("Leejam Sports","Fitness Time"),
    ("BinDawood Holding","Danube"),("United Electronics","eXtra"),
    ("Cenomi Retail","Cenomi"),("Arabian Food Industries","Domty"),
    ("SASCO","SASCO Energy"),("Nana Direct","Nana"),
]
CHART_TYPES = ["Bar","Line","Area","Horizontal Bar","Pie","Donut","Scatter"]

# ── Helpers ─────────────────────────────────────────────────────────────────────
def days_since(d):
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    return (date.today() - d).days

def rnd_date(max_days):
    return date.today() - timedelta(days=random.randint(0, max_days))

def initials(name):
    parts = name.split()
    return "".join(p[0] for p in parts[:2]).upper()

def urgency_badge(days):
    if days > 30:
        return f'<span class="badge-danger">{days}d ago</span>'
    elif days > 14:
        return f'<span class="badge-warn">{days}d ago</span>'
    return f'<span class="badge-success">{days}d ago</span>'

def role_badge(role):
    return f'<span class="role-{role}">{ROLES[role]["label"]}</span>'

def has_perm(role, perm):
    return perm in ROLES.get(role, {}).get("perms", set())

# ── State initialization ────────────────────────────────────────────────────────
def init_state():
    if "initialized" in st.session_state:
        return

    # Users
    st.session_state.users = [
        {"id":"u1","name":"Ahmed Al-Harbi",   "role":"admin",   "email":"ahmed@corp.com",    **TEAM_COLORS[0]},
        {"id":"u2","name":"Sara Al-Zahrani",   "role":"manager", "email":"sara@corp.com",     **TEAM_COLORS[1]},
        {"id":"u3","name":"Mohammed Al-Ghamdi","role":"rep",     "email":"mohammed@corp.com", **TEAM_COLORS[2]},
        {"id":"u4","name":"Fatima Al-Otaibi",  "role":"rep",     "email":"fatima@corp.com",   **TEAM_COLORS[3]},
        {"id":"u5","name":"Khalid Al-Qahtani", "role":"viewer",  "email":"khalid@corp.com",   **TEAM_COLORS[4]},
    ]
    st.session_state.active_user_id = "u1"

    # Call statuses
    st.session_state.call_statuses = [
        {"id":"cs1","label":"Completed",           "color":"#1D9E75"},
        {"id":"cs2","label":"No Answer",            "color":"#BA7517"},
        {"id":"cs3","label":"Follow-up Required",   "color":"#185FA5"},
        {"id":"cs4","label":"Meeting Scheduled",    "color":"#534AB7"},
        {"id":"cs5","label":"Not Interested",       "color":"#A32D2D"},
        {"id":"cs6","label":"Voicemail Left",       "color":"#5F5E5A"},
    ]

    # Extra fields
    st.session_state.account_extra_fields = [
        {"id":"ef1","label":"Region",   "type":"text",   "options":[]},
        {"id":"ef2","label":"Priority", "type":"select", "options":["High","Medium","Low"]},
    ]
    st.session_state.user_extra_fields = [
        {"id":"uf1","label":"Phone",     "type":"text","options":[]},
        {"id":"uf2","label":"Territory", "type":"text","options":[]},
    ]
    st.session_state.call_extra_fields = [
        {"id":"cf1","label":"Deal Size", "type":"text","options":[]},
        {"id":"cf2","label":"Next Step", "type":"text","options":[]},
    ]

    # Generate mock accounts with notes
    accounts = []
    all_notes = _gen_mock_notes()
    for i, (acc_name, brand) in enumerate(BRANDS):
        my_notes = [n for j, n in enumerate(all_notes) if j % len(BRANDS) == i][:3]
        last_call = my_notes[0]["date"] if my_notes else str(rnd_date(45))
        accounts.append({
            "id": f"ACC-{str(i+1).zfill(4)}",
            "account_name": acc_name,
            "brand_name": brand,
            "branches": random.randint(3, 120),
            "sector": SECTORS[i % len(SECTORS)],
            "last_call_date": last_call,
            "contact_person": f"{['Ahmed','Sara','Mohammed','Fatima','Khalid'][i%5]} {['Al-Harbi','Al-Zahrani','Al-Ghamdi','Al-Otaibi','Al-Qahtani'][i%5]}",
            "notes": my_notes,
            "extra_fields": {"ef1": "", "ef2": "Medium"},
        })
    st.session_state.accounts = accounts
    st.session_state.initialized = True

def _gen_mock_notes():
    users = [{"id":"u1"},{"id":"u2"},{"id":"u3"},{"id":"u4"},{"id":"u5"}]
    statuses = ["cs1","cs2","cs3","cs4","cs5","cs6"]
    notes = []
    today = date.today()
    for i in range(89, -1, -1):
        d = today - timedelta(days=i)
        for _ in range(random.randint(0, 3)):
            notes.append({
                "date": str(d),
                "text": "Follow-up call.",
                "member_id": random.choice(users)["id"],
                "status_id": random.choice(statuses),
                "extra_fields": {"cf1":"","cf2":""},
            })
    return notes

# ── Active user helpers ─────────────────────────────────────────────────────────
def get_active_user():
    uid = st.session_state.active_user_id
    return next((u for u in st.session_state.users if u["id"] == uid), st.session_state.users[0])

def get_user(uid):
    return next((u for u in st.session_state.users if u["id"] == uid), None)

def get_status(sid):
    return next((s for s in st.session_state.call_statuses if s["id"] == sid), None)

# ── All logs helper ─────────────────────────────────────────────────────────────
def get_all_logs(filter_user_id=None):
    logs = []
    for acc in st.session_state.accounts:
        for note in acc["notes"]:
            if filter_user_id and note.get("member_id") != filter_user_id:
                continue
            logs.append({**note, "account_id": acc["id"], "account_name": acc["account_name"], "brand_name": acc["brand_name"]})
    return sorted(logs, key=lambda x: x["date"], reverse=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
def render_sidebar():
    active = get_active_user()
    st.sidebar.markdown("### Client Interaction Management")
    st.sidebar.markdown("---")

    # User switcher
    st.sidebar.markdown("**Active User**")
    user_names = [u["name"] for u in st.session_state.users]
    current_idx = next((i for i, u in enumerate(st.session_state.users) if u["id"] == active["id"]), 0)
    selected_name = st.sidebar.selectbox("Switch user", user_names, index=current_idx, label_visibility="collapsed")
    selected_user = next(u for u in st.session_state.users if u["name"] == selected_name)
    if selected_user["id"] != st.session_state.active_user_id:
        st.session_state.active_user_id = selected_user["id"]
        st.rerun()

    st.sidebar.markdown(
        f'{role_badge(active["role"])} &nbsp; **{active["name"]}**',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(f'<small style="color:#888">{active["email"]}</small>', unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Stats
    total = len(st.session_state.accounts)
    overdue = sum(1 for a in st.session_state.accounts if days_since(a["last_call_date"]) > 14)
    st.sidebar.metric("Total Accounts", total)
    st.sidebar.metric("Overdue (>14d)", overdue)
    st.sidebar.metric("Team Size", len(st.session_state.users))
    st.sidebar.markdown("---")
    st.sidebar.markdown('<small style="color:#aaa">Data resets on refresh. Connect a database for persistence.</small>', unsafe_allow_html=True)

# ── Dashboard Tab ───────────────────────────────────────────────────────────────
def render_dashboard(active, is_rep):
    if is_rep:
        st.markdown(
            f'<div class="rep-banner">My performance view — showing only your activity</div>',
            unsafe_allow_html=True,
        )

    logs = get_all_logs(filter_user_id=active["id"] if is_rep else None)
    accounts = st.session_state.accounts

    # Metrics
    if is_rep:
        my_accs = [a for a in accounts if any(n["member_id"] == active["id"] for n in a["notes"])]
        total = len(my_accs)
        c30 = sum(1 for a in my_accs if any(n["member_id"] == active["id"] and days_since(n["date"]) <= 30 for n in a["notes"]))
        tb = sum(a["branches"] for a in my_accs) or 1
        cb = sum(a["branches"] for a in my_accs if any(n["member_id"] == active["id"] and days_since(n["date"]) <= 30 for n in a["notes"]))
        week_calls = sum(1 for l in logs if days_since(l["date"]) <= 7)
    else:
        total = len(accounts)
        c30 = sum(1 for a in accounts if days_since(a["last_call_date"]) <= 30)
        tb = sum(a["branches"] for a in accounts) or 1
        cb = sum(a["branches"] for a in accounts if days_since(a["last_call_date"]) <= 30)
        week_calls = None

    cov = round(c30 / total * 100) if total else 0
    br = round(cb / tb * 100) if tb else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Coverage (30d)", f"{cov}%", f"{c30}/{total} accounts")
    if is_rep:
        col2.metric("My calls this week", week_calls, f"{len(logs)} total")
    else:
        overdue = sum(1 for a in accounts if days_since(a["last_call_date"]) > 14)
        col2.metric("Overdue >14d", overdue, "need contact")
    col3.metric("Total branches", f"{tb:,}", "under management")
    col4.metric("Branch coverage", f"{br}%", f"{cb:,} contacted")

    st.markdown("---")

    # Chart
    render_chart(logs, is_rep)

    st.markdown("---")

    # Urgency list (non-rep only)
    if not is_rep:
        st.subheader("Top priority — overdue accounts")
        urgency = sorted(
            [a for a in accounts if days_since(a["last_call_date"]) > 14],
            key=lambda x: days_since(x["last_call_date"]), reverse=True
        )[:5]
        if not urgency:
            st.info("All accounts contacted in the last 14 days.")
        else:
            for acc in urgency:
                d = days_since(acc["last_call_date"])
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{acc['brand_name']}** &nbsp; <small style='color:#888'>{acc['account_name']} · {acc['branches']} branches</small>", unsafe_allow_html=True)
                c2.markdown(urgency_badge(d), unsafe_allow_html=True)
                if has_perm(active["role"], "log"):
                    if c3.button("Log call", key=f"dash_log_{acc['id']}"):
                        st.session_state.log_target = acc["id"]
                        st.session_state.show_log_modal = True
                        st.rerun()

# ── Chart renderer ──────────────────────────────────────────────────────────────
def render_chart(logs, is_rep):
    st.subheader("Call activity")

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        granularity = st.selectbox("Granularity", ["Daily","Weekly","Monthly","Yearly"], index=1, key="chart_gran")
    with c2:
        chart_type = st.selectbox("Chart type", CHART_TYPES, index=0, key="chart_type")
    with c3:
        range_offset = st.number_input("← Periods back", min_value=0, max_value=24, value=0, step=1, key="chart_offset")

    users = st.session_state.users
    today = date.today()

    # Build period buckets
    if granularity == "Daily":
        size = 14
        periods = [(today - timedelta(days=i + range_offset * size)).strftime("%Y-%m-%d")
                   for i in range(size - 1, -1, -1)]
        labels = [(today - timedelta(days=i + range_offset * size)).strftime("%d/%m")
                  for i in range(size - 1, -1, -1)]
        def bucket(log_date): return log_date[:10]
    elif granularity == "Weekly":
        size = 8
        def week_start(d):
            if isinstance(d, str): d = datetime.strptime(d, "%Y-%m-%d").date()
            return (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")
        periods = []
        for i in range(size - 1, -1, -1):
            d = today - timedelta(weeks=i + range_offset * size)
            periods.append(week_start(d))
        periods = list(dict.fromkeys(periods))
        labels = [datetime.strptime(p, "%Y-%m-%d").strftime("%b %d") for p in periods]
        def bucket(log_date): return week_start(log_date[:10])
    elif granularity == "Monthly":
        size = 12
        periods = []
        for i in range(size - 1, -1, -1):
            m = today.month - i - range_offset * size
            y = today.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            periods.append(f"{y}-{str(m).zfill(2)}")
        labels = [datetime.strptime(p+"-01","%Y-%m-%d").strftime("%b %Y") for p in periods]
        def bucket(log_date): return log_date[:7]
    else:  # Yearly
        size = 4
        years = [str(today.year - i - range_offset * size) for i in range(size - 1, -1, -1)]
        periods = years
        labels = years
        def bucket(log_date): return log_date[:4]

    # Build DataFrame
    rows = []
    visible_users = [u for u in users if not is_rep or u["id"] == st.session_state.active_user_id]
    for u in visible_users:
        for p, label in zip(periods, labels):
            count = sum(1 for l in logs if bucket(l["date"]) == p and l["member_id"] == u["id"])
            rows.append({"Period": label, "User": u["name"].split()[0], "Calls": count, "Color": u["color"]})
    df = pd.DataFrame(rows)

    if df.empty or df["Calls"].sum() == 0:
        st.info("No call data for this period.")
        return

    color_map = {u["name"].split()[0]: u["color"] for u in visible_users}
    user_names = [u["name"].split()[0] for u in visible_users]

    ct = chart_type
    if ct == "Bar":
        fig = px.bar(df, x="Period", y="Calls", color="User", color_discrete_map=color_map, barmode="stack")
    elif ct == "Line":
        fig = px.line(df, x="Period", y="Calls", color="User", color_discrete_map=color_map, markers=True)
    elif ct == "Area":
        fig = px.area(df, x="Period", y="Calls", color="User", color_discrete_map=color_map)
    elif ct == "Horizontal Bar":
        fig = px.bar(df, y="Period", x="Calls", color="User", color_discrete_map=color_map, barmode="stack", orientation="h")
    elif ct == "Pie":
        df_agg = df.groupby("User")["Calls"].sum().reset_index()
        fig = px.pie(df_agg, values="Calls", names="User", color="User", color_discrete_map=color_map)
    elif ct == "Donut":
        df_agg = df.groupby("User")["Calls"].sum().reset_index()
        fig = px.pie(df_agg, values="Calls", names="User", color="User", color_discrete_map=color_map, hole=0.4)
    else:  # Scatter
        fig = px.scatter(df, x="Period", y="Calls", color="User", color_discrete_map=color_map, size="Calls",
                         size_max=18)

    fig.update_layout(
        height=300, margin=dict(l=10,r=10,t=20,b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Accounts Tab ────────────────────────────────────────────────────────────────
def render_accounts(active, is_rep):
    st.subheader("My accounts" if is_rep else "All accounts")

    search = st.text_input("Search by name, brand, or ID", placeholder="Type to filter…", key="acc_search")
    sort_col, sort_dir_col = st.columns([2, 1])
    sort_by = sort_col.selectbox("Sort by", ["last_call_date","account_name","brand_name","branches"], key="sort_by")
    sort_asc = sort_dir_col.selectbox("Order", ["Ascending","Descending"], key="sort_dir") == "Ascending"

    accounts = st.session_state.accounts
    if is_rep:
        accounts = [a for a in accounts if any(n["member_id"] == active["id"] for n in a["notes"])]
    if search:
        q = search.lower()
        accounts = [a for a in accounts if q in a["account_name"].lower() or q in a["brand_name"].lower() or q in a["id"].lower()]
    accounts = sorted(accounts, key=lambda x: str(x.get(sort_by,"")), reverse=not sort_asc)

    st.caption(f"{len(accounts)} accounts")

    for acc in accounts:
        d = days_since(acc["last_call_date"])
        last_note = acc["notes"][0] if acc["notes"] else None
        last_by = ""
        if last_note:
            u = get_user(last_note.get("member_id",""))
            last_by = u["name"].split()[0] if u else "—"

        with st.expander(f"**{acc['brand_name']}** &nbsp;·&nbsp; {acc['account_name']} &nbsp;·&nbsp; {acc['branches']} branches", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"**ID:** `{acc['id']}`")
            col2.markdown(f"**Sector:** {acc['sector']}")
            col3.markdown(f"**Contact:** {acc.get('contact_person','—')}")
            col4.markdown(f"**Last call:** {acc['last_call_date']}")
            st.markdown(f"**Days since last call:** " + urgency_badge(d) + f" &nbsp; **Last logged by:** {last_by}", unsafe_allow_html=True)

            # Extra fields
            ef = acc.get("extra_fields",{})
            for field in st.session_state.account_extra_fields:
                val = ef.get(field["id"],"")
                if val:
                    st.markdown(f"**{field['label']}:** {val}")

            # Interaction history
            if acc["notes"]:
                st.markdown("**Recent interactions:**")
                for note in acc["notes"][:3]:
                    u = get_user(note.get("member_id",""))
                    s = get_status(note.get("status_id",""))
                    uname = u["name"].split()[0] if u else "—"
                    slabel = s["label"] if s else ""
                    st.markdown(f"&nbsp;&nbsp;&nbsp;`{note['date']}` &nbsp; **{uname}** &nbsp; {slabel}" + (f" — {note['text']}" if note.get("text") else ""))

            if has_perm(active["role"],"log"):
                if st.button("Log call", key=f"acc_log_{acc['id']}"):
                    st.session_state.log_target = acc["id"]
                    st.session_state.show_log_modal = True
                    st.rerun()

# ── Urgency Tab ─────────────────────────────────────────────────────────────────
def render_urgency(active):
    st.subheader("Accounts not contacted in 14+ days")
    urgency = sorted(
        [a for a in st.session_state.accounts if days_since(a["last_call_date"]) > 14],
        key=lambda x: days_since(x["last_call_date"]), reverse=True
    )
    st.caption(f"{len(urgency)} accounts overdue")
    if not urgency:
        st.success("All accounts contacted recently.")
        return

    for acc in urgency:
        d = days_since(acc["last_call_date"])
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        c1.markdown(f"**{acc['brand_name']}** `{acc['id']}`")
        c2.markdown(f"<small>{acc['account_name']} · {acc['branches']} branches</small>", unsafe_allow_html=True)
        c3.markdown(urgency_badge(d), unsafe_allow_html=True)
        if has_perm(active["role"],"log"):
            if c4.button("Log call", key=f"urg_log_{acc['id']}"):
                st.session_state.log_target = acc["id"]
                st.session_state.show_log_modal = True
                st.rerun()
        st.divider()

# ── Activity Log Tab ────────────────────────────────────────────────────────────
def render_log(active, is_rep):
    st.subheader("My interaction log" if is_rep else "Interaction log")
    logs = get_all_logs(filter_user_id=active["id"] if is_rep else None)
    st.caption(f"{len(logs)} entries")
    if not logs:
        st.info("No interactions logged yet.")
        return

    rows = []
    for l in logs:
        u = get_user(l.get("member_id",""))
        s = get_status(l.get("status_id",""))
        rows.append({
            "Date": l["date"],
            "Brand": l["brand_name"],
            "Account": l["account_name"],
            "Team Member": u["name"] if u else "—",
            "Status": s["label"] if s else "—",
            "Notes": l.get("text",""),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if has_perm(active["role"],"export"):
        csv = df.to_csv(index=False).encode()
        st.download_button("Export log as CSV", csv, "activity_log.csv", "text/csv")

# ── Users Tab ───────────────────────────────────────────────────────────────────
def render_users(active):
    is_admin = has_perm(active["role"], "manage_users")
    st.subheader("User management" if is_admin else "Team members")

    # User list
    for u in st.session_state.users:
        c1, c2, c3 = st.columns([3, 1, 2]) if is_admin else st.columns([4, 1, 1])
        c1.markdown(
            f"**{u['name']}** &nbsp; <small style='color:#888'>{u['email']}</small>",
            unsafe_allow_html=True,
        )
        c2.markdown(role_badge(u["role"]), unsafe_allow_html=True)
        if is_admin:
            btn_cols = c3.columns(2)
            if btn_cols[0].button("Edit", key=f"edit_user_{u['id']}"):
                st.session_state.editing_user = u["id"]
                st.rerun()
            if u["id"] != active["id"]:
                if btn_cols[1].button("Remove", key=f"del_user_{u['id']}"):
                    st.session_state.users = [x for x in st.session_state.users if x["id"] != u["id"]]
                    st.rerun()
        st.divider()

    if is_admin:
        if st.button("+ Add user", type="primary"):
            st.session_state.editing_user = "__new__"
            st.rerun()

    # Edit / Add user form
    if st.session_state.get("editing_user"):
        uid = st.session_state.editing_user
        existing = next((u for u in st.session_state.users if u["id"] == uid), None) if uid != "__new__" else None
        st.markdown("---")
        st.subheader("Edit user" if existing else "Add user")

        with st.form("user_form"):
            name = st.text_input("Full name", value=existing["name"] if existing else "")
            email = st.text_input("Email", value=existing["email"] if existing else "")
            role_options = list(ROLES.keys())
            role_idx = role_options.index(existing["role"]) if existing else 2
            if existing and existing["id"] == active["id"]:
                st.selectbox("Role", role_options, index=role_idx, disabled=True, format_func=lambda r: ROLES[r]["label"])
                role = existing["role"]
                st.caption("You cannot change your own role.")
            else:
                role = st.selectbox("Role", role_options, index=role_idx, format_func=lambda r: ROLES[r]["label"])

            # Extra user fields
            ef_vals = {}
            for f in st.session_state.user_extra_fields:
                default = existing.get("extra_fields",{}).get(f["id"],"") if existing else ""
                if f["type"] == "select":
                    ef_vals[f["id"]] = st.selectbox(f["label"], [""] + f["options"], index=0)
                else:
                    ef_vals[f["id"]] = st.text_input(f["label"], value=default)

            col1, col2 = st.columns(2)
            save = col1.form_submit_button("Save", type="primary")
            cancel = col2.form_submit_button("Cancel")

        if save and name:
            color = TEAM_COLORS[len(st.session_state.users) % len(TEAM_COLORS)]
            new_user = {
                "id": existing["id"] if existing else "u" + str(len(st.session_state.users)+1),
                "name": name, "email": email, "role": role,
                "extra_fields": ef_vals,
                **({"color": existing["color"], "bg": existing["bg"]} if existing else color),
            }
            if existing:
                st.session_state.users = [new_user if u["id"] == existing["id"] else u for u in st.session_state.users]
            else:
                st.session_state.users.append(new_user)
            del st.session_state["editing_user"]
            st.rerun()
        if cancel:
            del st.session_state["editing_user"]
            st.rerun()

    # Permissions matrix
    st.markdown("---")
    st.subheader("Role permissions")
    perm_data = {}
    for perm_key, perm_label in ROLE_PERMS_LABELS:
        perm_data[perm_label] = {ROLES[r]["label"]: ("✓" if perm_key in ROLES[r]["perms"] else "✕") for r in ROLES}
    df_perms = pd.DataFrame(perm_data).T
    st.dataframe(df_perms, use_container_width=True)

# ── Field Builder Tab ───────────────────────────────────────────────────────────
def render_schema():
    st.subheader("Field builder")

    # Custom fields
    all_fields = (
        [(f, "Account") for f in st.session_state.account_extra_fields] +
        [(f, "User")    for f in st.session_state.user_extra_fields] +
        [(f, "Call")    for f in st.session_state.call_extra_fields]
    )

    st.markdown("**Custom fields**")
    if not all_fields:
        st.caption("No custom fields yet.")
    else:
        for f, entity in all_fields:
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(f"**{f['label']}**")
            c2.markdown(f"`{f['type']}`")
            c3.markdown(f'<span class="badge-info">{entity}</span>', unsafe_allow_html=True)
            if c4.button("Remove", key=f"del_field_{f['id']}"):
                if entity == "Account":
                    st.session_state.account_extra_fields = [x for x in st.session_state.account_extra_fields if x["id"] != f["id"]]
                elif entity == "User":
                    st.session_state.user_extra_fields = [x for x in st.session_state.user_extra_fields if x["id"] != f["id"]]
                else:
                    st.session_state.call_extra_fields = [x for x in st.session_state.call_extra_fields if x["id"] != f["id"]]
                st.rerun()

    st.markdown("---")
    st.markdown("**Add new field**")
    with st.form("add_field_form"):
        fc1, fc2, fc3 = st.columns(3)
        label = fc1.text_input("Label", placeholder="Field label")
        ftype = fc2.selectbox("Type", ["text","number","date","select"])
        entity = fc3.selectbox("Applies to", ["Account","User","Call"])
        options_str = ""
        if ftype == "select":
            options_str = st.text_input("Options (comma-separated)", placeholder="High,Medium,Low")
        if st.form_submit_button("Add field", type="primary") and label:
            new_field = {"id":"f"+str(len(all_fields)+1)+"_"+str(random.randint(100,999)), "label":label, "type":ftype, "options":[o.strip() for o in options_str.split(",") if o.strip()]}
            if entity == "Account":
                st.session_state.account_extra_fields.append(new_field)
            elif entity == "User":
                st.session_state.user_extra_fields.append(new_field)
            else:
                st.session_state.call_extra_fields.append(new_field)
            st.rerun()

    # Call statuses
    st.markdown("---")
    st.markdown("**Call status options**")
    for s in st.session_state.call_statuses:
        c1, c2 = st.columns([4,1])
        c1.markdown(f'<span style="display:inline-flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:{s["color"]};display:inline-block"></span>{s["label"]}</span>', unsafe_allow_html=True)
        if c2.button("Remove", key=f"del_status_{s['id']}"):
            st.session_state.call_statuses = [x for x in st.session_state.call_statuses if x["id"] != s["id"]]
            st.rerun()

    st.markdown("**Add status**")
    with st.form("add_status_form"):
        sc1, sc2 = st.columns([3,1])
        new_label = sc1.text_input("Label", placeholder="Status label")
        new_color = sc2.color_picker("Color", "#378ADD")
        if st.form_submit_button("Add status", type="primary") and new_label:
            st.session_state.call_statuses.append({"id":"cs_"+str(random.randint(1000,9999)), "label":new_label, "color":new_color})
            st.rerun()

# ── Log Call Modal ──────────────────────────────────────────────────────────────
def render_log_modal(active):
    if not st.session_state.get("show_log_modal"):
        return

    acc_id = st.session_state.get("log_target")
    acc = next((a for a in st.session_state.accounts if a["id"] == acc_id), None)
    if not acc:
        return

    st.markdown("---")
    st.subheader(f"Log interaction — {acc['brand_name']}")
    st.caption(f"{acc['account_name']} · {acc['branches']} branches · Last call: {acc['last_call_date']}")

    with st.form("log_form"):
        col1, col2 = st.columns(2)
        user_names = [u["name"] for u in st.session_state.users]
        default_idx = next((i for i,u in enumerate(st.session_state.users) if u["id"] == active["id"]),0)
        member_name = col1.selectbox("Team member", user_names, index=default_idx)
        call_date = col2.date_input("Call date", value=date.today(), max_value=date.today())

        status_labels = [s["label"] for s in st.session_state.call_statuses]
        status_label = st.selectbox("Call status", status_labels if status_labels else ["—"])

        # Call extra fields
        ef_vals = {}
        for f in st.session_state.call_extra_fields:
            if f["type"] == "select":
                ef_vals[f["id"]] = st.selectbox(f["label"], [""] + f["options"])
            else:
                ef_vals[f["id"]] = st.text_input(f["label"], placeholder=f["label"])

        notes_text = st.text_area("Notes", placeholder="Brief note about the interaction…", height=80)

        c1, c2 = st.columns(2)
        save = c1.form_submit_button("Save log", type="primary")
        cancel = c2.form_submit_button("Cancel")

    if save:
        member = next((u for u in st.session_state.users if u["name"] == member_name), None)
        status = next((s for s in st.session_state.call_statuses if s["label"] == status_label), None)
        new_note = {
            "date": str(call_date),
            "text": notes_text,
            "member_id": member["id"] if member else "",
            "status_id": status["id"] if status else "",
            "extra_fields": ef_vals,
        }
        for a in st.session_state.accounts:
            if a["id"] == acc_id:
                a["notes"].insert(0, new_note)
                a["last_call_date"] = str(call_date)
                break
        st.session_state.show_log_modal = False
        st.session_state.log_target = None
        st.success(f"Call logged for {acc['brand_name']}")
        st.rerun()

    if cancel:
        st.session_state.show_log_modal = False
        st.session_state.log_target = None
        st.rerun()

# ── Add Account Form ────────────────────────────────────────────────────────────
def render_add_account(active):
    if not st.session_state.get("show_add_account"):
        return

    st.markdown("---")
    st.subheader("Add new account")
    with st.form("add_account_form"):
        c1, c2 = st.columns(2)
        acc_name = c1.text_input("Account name (legal)", placeholder="Legal entity name")
        brand = c2.text_input("Brand name", placeholder="Public-facing name")
        c3, c4 = st.columns(2)
        branches = c3.number_input("# of branches", min_value=1, value=10)
        sector = c4.selectbox("Sector", SECTORS)
        contact = st.text_input("Contact person", placeholder="Primary contact name")

        ef_vals = {}
        for f in st.session_state.account_extra_fields:
            if f["type"] == "select":
                ef_vals[f["id"]] = st.selectbox(f["label"], [""] + f["options"])
            else:
                ef_vals[f["id"]] = st.text_input(f["label"])

        c1, c2 = st.columns(2)
        save = c1.form_submit_button("Add account", type="primary")
        cancel = c2.form_submit_button("Cancel")

    if save and acc_name and brand:
        new_acc = {
            "id": f"ACC-{str(len(st.session_state.accounts)+1).zfill(4)}",
            "account_name": acc_name, "brand_name": brand,
            "branches": int(branches), "sector": sector,
            "last_call_date": str(rnd_date(50)),
            "contact_person": contact, "notes": [], "extra_fields": ef_vals,
        }
        st.session_state.accounts.append(new_acc)
        st.session_state.show_add_account = False
        st.success(f"Account '{brand}' added.")
        st.rerun()
    if cancel:
        st.session_state.show_add_account = False
        st.rerun()

# ── Import CSV ──────────────────────────────────────────────────────────────────
def render_import(active):
    if not st.session_state.get("show_import"):
        return

    st.markdown("---")
    st.subheader("Import accounts — CSV")

    mode = st.radio("Mode", ["Add new rows","Update existing by Account ID"], horizontal=True)
    uploaded = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded:
        df = pd.read_csv(uploaded)
        st.caption(f"{len(df)} rows detected")
        st.dataframe(df.head(5), use_container_width=True)

        if st.button("Import", type="primary"):
            count = 0
            for _, row in df.iterrows():
                acc_name = str(row.get("Account Name","")).strip()
                brand = str(row.get("Brand Name","")).strip()
                if not acc_name or not brand:
                    continue
                acc_id = str(row.get("Account ID","")).strip() or f"ACC-{str(len(st.session_state.accounts)+count+1).zfill(4)}"
                existing = next((a for a in st.session_state.accounts if a["id"] == acc_id), None)
                new_acc = {
                    "id": acc_id, "account_name": acc_name, "brand_name": brand,
                    "branches": int(row.get("# of Branches",0) or 0),
                    "sector": str(row.get("Sector","Retail")),
                    "contact_person": str(row.get("Contact Person","")),
                    "last_call_date": str(row.get("Last Call Date", str(rnd_date(50)))),
                    "notes": existing["notes"] if existing else [],
                    "extra_fields": {},
                }
                if "Update" in mode and existing:
                    idx = st.session_state.accounts.index(existing)
                    st.session_state.accounts[idx] = new_acc
                elif "Add" in mode or not existing:
                    st.session_state.accounts.append(new_acc)
                count += 1
            st.success(f"{count} accounts imported.")
            st.session_state.show_import = False
            st.rerun()

    # Template download
    template_df = pd.DataFrame(columns=["Account ID","Account Name","Brand Name","# of Branches","Sector","Contact Person"])
    csv_bytes = template_df.to_csv(index=False).encode()
    st.download_button("Download CSV template", csv_bytes, "accounts_template.csv", "text/csv")

    if st.button("Close"):
        st.session_state.show_import = False
        st.rerun()

# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    init_state()
    active = get_active_user()
    is_rep = active["role"] == "rep"

    render_sidebar()

    # Top action bar
    top_cols = st.columns([4, 1, 1, 1])
    top_cols[0].title("Client Interaction Management")
    with top_cols[1]:
        if has_perm(active["role"],"import") and st.button("Import CSV", use_container_width=True):
            st.session_state.show_import = True
            st.session_state.show_add_account = False
            st.session_state.show_log_modal = False
    with top_cols[2]:
        if has_perm(active["role"],"add_account") and st.button("+ Account", type="primary", use_container_width=True):
            st.session_state.show_add_account = True
            st.session_state.show_import = False
            st.session_state.show_log_modal = False

    # Render inline forms if open
    render_add_account(active)
    render_import(active)
    render_log_modal(active)

    # Tab count labels
    urgency_count = sum(1 for a in st.session_state.accounts if days_since(a["last_call_date"]) > 14)
    tab_labels = ["Dashboard","Accounts",f"Urgency ({urgency_count})","Activity Log","Users"]
    if has_perm(active["role"],"manage_schema"):
        tab_labels.append("Field Builder")

    tabs = st.tabs(tab_labels)

    with tabs[0]: render_dashboard(active, is_rep)
    with tabs[1]: render_accounts(active, is_rep)
    with tabs[2]: render_urgency(active)
    with tabs[3]: render_log(active, is_rep)
    with tabs[4]: render_users(active)
    if has_perm(active["role"],"manage_schema") and len(tabs) > 5:
        with tabs[5]: render_schema()


if __name__ == "__main__":
    main()
