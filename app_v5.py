"""
Client Interaction Management System (CIMS) — v5
Streamlit application. Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
import random
import uuid

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Client Interaction Management",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main .block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1150px}
    .stTabs [data-baseweb="tab-list"]{gap:4px}
    .stTabs [data-baseweb="tab"]{border-radius:8px;padding:5px 13px}
    .badge-success{background:#EAF3DE;color:#27500A;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:500}
    .badge-warn{background:#FAEEDA;color:#633806;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:500}
    .badge-danger{background:#FCEBEB;color:#791F1F;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:500}
    .badge-info{background:#E6F1FB;color:#0C447C;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:500}
    .rep-banner{background:#E6F1FB;color:#0C447C;padding:10px 14px;border-radius:8px;margin-bottom:1rem;font-size:13px}
    .section-box{border:1px solid #e8e6de;border-radius:10px;padding:16px;margin-bottom:12px}
    div[data-testid="stMetricValue"]>div{font-size:1.5rem!important}
    .stDataFrame{border-radius:10px;overflow:hidden}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
ALL_PERMS = [
    ("view",           "View accounts"),
    ("log",            "Log calls"),
    ("add_account",    "Add/Edit/Delete accounts"),
    ("import",         "Import CSV"),
    ("manage_users",   "Manage users"),
    ("export",         "Export data"),
    ("manage_schema",  "Manage fields & roles"),
]
TEAM_COLORS = [
    {"color":"#185FA5","bg":"#E6F1FB"},{"color":"#0F6E56","bg":"#E1F5EE"},
    {"color":"#993C1D","bg":"#FAECE7"},{"color":"#993556","bg":"#FBEAF0"},
    {"color":"#854F0B","bg":"#FAEEDA"},{"color":"#534AB7","bg":"#EEEDFE"},
    {"color":"#3B6D11","bg":"#EAF3DE"},{"color":"#A32D2D","bg":"#FCEBEB"},
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
CHART_TYPES = ["Bar","Stacked Bar","Line","Area","Horizontal Bar","Pie","Donut","Scatter"]

# ── Helpers ────────────────────────────────────────────────────────────────────
def uid(): return str(uuid.uuid4())[:8]
def days_since(d):
    if not d: return 999
    try:
        if isinstance(d,str): d = datetime.strptime(d,"%Y-%m-%d").date()
        return (date.today()-d).days
    except: return 999
def rnd_date(n): return str(date.today()-timedelta(days=random.randint(0,n)))
def initials(name): return "".join(p[0] for p in name.split()[:2]).upper()
def gen_id(prefix,lst): return f"{prefix}-{str(len(lst)+1).zfill(4)}"

def urgency_badge(d):
    if d>30: return f'<span class="badge-danger">{d}d ago</span>'
    if d>14: return f'<span class="badge-warn">{d}d ago</span>'
    return f'<span class="badge-success">{d}d ago</span>'

def role_label(role_id):
    r = next((r for r in st.session_state.roles if r["id"]==role_id), None)
    return r["label"] if r else role_id

def role_badge_html(role_id):
    r = next((r for r in st.session_state.roles if r["id"]==role_id), None)
    if not r: return role_id
    color = r.get("color","#888"); bg = r.get("bg","#f0f0f0")
    return f'<span style="background:{bg};color:{color};padding:2px 9px;border-radius:20px;font-size:12px;font-weight:500">{r["label"]}</span>'

def has_perm(role_id, perm):
    r = next((r for r in st.session_state.roles if r["id"]==role_id), None)
    return perm in (r.get("perms") or set()) if r else False

def get_active_user():
    uid_ = st.session_state.get("active_user_id","u1")
    return next((u for u in st.session_state.users if u["id"]==uid_), st.session_state.users[0])

def get_user(uid_): return next((u for u in st.session_state.users if u["id"]==uid_), None)
def get_status(sid): return next((s for s in st.session_state.call_statuses if s["id"]==sid), None)

def get_all_logs(user_id=None):
    logs=[]
    for a in st.session_state.accounts:
        for n in a.get("notes",[]):
            if user_id and n.get("member_id")!=user_id: continue
            logs.append({**n,"account_id":a["id"],"account_name":a["account_name"],"brand_name":a["brand_name"]})
    return sorted(logs,key=lambda x:x.get("date",""),reverse=True)

# ── State init ─────────────────────────────────────────────────────────────────
def init_state():
    if "initialized" in st.session_state: return

    st.session_state.roles = [
        {"id":"admin",  "label":"Admin",   "color":"#3C3489","bg":"#EEEDFE","perms":{"view","log","add_account","import","manage_users","export","manage_schema"}},
        {"id":"manager","label":"Manager", "color":"#085041","bg":"#E1F5EE","perms":{"view","log","add_account","import","export"}},
        {"id":"rep",    "label":"Rep",     "color":"#633806","bg":"#FAEEDA","perms":{"view","log"}},
        {"id":"viewer", "label":"Viewer",  "color":"#444441","bg":"#F1EFE8","perms":{"view"}},
    ]
    st.session_state.users = [
        {"id":"u1","name":"Ahmed Al-Harbi",   "role":"admin",  "email":"ahmed@corp.com",   **TEAM_COLORS[0]},
        {"id":"u2","name":"Sara Al-Zahrani",   "role":"manager","email":"sara@corp.com",    **TEAM_COLORS[1]},
        {"id":"u3","name":"Mohammed Al-Ghamdi","role":"rep",    "email":"mohammed@corp.com",**TEAM_COLORS[2]},
        {"id":"u4","name":"Fatima Al-Otaibi",  "role":"rep",    "email":"fatima@corp.com",  **TEAM_COLORS[3]},
        {"id":"u5","name":"Khalid Al-Qahtani", "role":"viewer", "email":"khalid@corp.com",  **TEAM_COLORS[4]},
    ]
    st.session_state.active_user_id = "u1"
    st.session_state.call_statuses = [
        {"id":"cs1","label":"Completed",         "color":"#1D9E75"},
        {"id":"cs2","label":"No Answer",          "color":"#BA7517"},
        {"id":"cs3","label":"Follow-up Required", "color":"#185FA5"},
        {"id":"cs4","label":"Meeting Scheduled",  "color":"#534AB7"},
        {"id":"cs5","label":"Not Interested",     "color":"#A32D2D"},
        {"id":"cs6","label":"Voicemail Left",     "color":"#5F5E5A"},
    ]
    st.session_state.account_extra_fields = [
        {"id":"ef1","label":"Region",  "type":"text",  "options":[]},
        {"id":"ef2","label":"Priority","type":"select","options":["High","Medium","Low"]},
    ]
    st.session_state.user_extra_fields = [
        {"id":"uf1","label":"Phone",    "type":"text","options":[]},
        {"id":"uf2","label":"Territory","type":"text","options":[]},
    ]
    st.session_state.call_extra_fields = [
        {"id":"cf1","label":"Deal Size","type":"text","options":[]},
        {"id":"cf2","label":"Next Step","type":"text","options":[]},
    ]

    # Mock data
    pool = _gen_mock_notes()
    accounts=[]
    for i,(acc_name,brand) in enumerate(BRANDS):
        my_notes=[n for j,n in enumerate(pool) if j%len(BRANDS)==i][:3]
        last=my_notes[0]["date"] if my_notes else rnd_date(45)
        accounts.append({
            "id":f"ACC-{str(i+1).zfill(4)}","account_name":acc_name,"brand_name":brand,
            "branches":random.randint(3,120),"sector":SECTORS[i%len(SECTORS)],
            "last_call_date":last,
            "contact_person":f"{['Ahmed','Sara','Mohammed','Fatima','Khalid'][i%5]} {['Al-Harbi','Al-Zahrani','Al-Ghamdi','Al-Otaibi','Al-Qahtani'][i%5]}",
            "notes":my_notes,"extra_fields":{"ef1":"","ef2":"Medium"},
        })
    st.session_state.accounts=accounts
    st.session_state.initialized=True

def _gen_mock_notes():
    uids=["u1","u2","u3","u4","u5"]; sids=["cs1","cs2","cs3","cs4","cs5","cs6"]
    notes=[]; today=date.today()
    for i in range(89,-1,-1):
        d=today-timedelta(days=i)
        for _ in range(random.randint(0,3)):
            notes.append({"date":str(d),"text":"Follow-up call.","member_id":random.choice(uids),"status_id":random.choice(sids),"extra_fields":{"cf1":"","cf2":""}})
    return notes

# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar():
    active=get_active_user()
    st.sidebar.markdown("### CIMS")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Switch user**")
    names=[u["name"] for u in st.session_state.users]
    idx=next((i for i,u in enumerate(st.session_state.users) if u["id"]==active["id"]),0)
    sel=st.sidebar.selectbox("User",names,index=idx,label_visibility="collapsed")
    sel_user=next(u for u in st.session_state.users if u["name"]==sel)
    if sel_user["id"]!=st.session_state.active_user_id:
        st.session_state.active_user_id=sel_user["id"]; st.rerun()

    st.sidebar.markdown(role_badge_html(active["role"])+" &nbsp; **"+active["name"]+"**",unsafe_allow_html=True)
    st.sidebar.markdown(f'<small style="color:#888">{active["email"]}</small>',unsafe_allow_html=True)
    st.sidebar.markdown("---")
    total=len(st.session_state.accounts)
    overdue=sum(1 for a in st.session_state.accounts if days_since(a["last_call_date"])>14)
    st.sidebar.metric("Accounts",total)
    st.sidebar.metric("Overdue >14d",overdue)
    st.sidebar.metric("Team",len(st.session_state.users))

# ── Dashboard ──────────────────────────────────────────────────────────────────
def render_dashboard(active,is_rep):
    if is_rep:
        st.markdown('<div class="rep-banner">My performance view — showing only your activity</div>',unsafe_allow_html=True)

    logs=get_all_logs(user_id=active["id"] if is_rep else None)
    accounts=st.session_state.accounts

    if is_rep:
        my_accs=[a for a in accounts if any(n["member_id"]==active["id"] for n in a.get("notes",[]))]
        total=len(my_accs); tb=sum(a["branches"] for a in my_accs) or 1
        c30=sum(1 for a in my_accs if any(n["member_id"]==active["id"] and days_since(n["date"])<=30 for n in a.get("notes",[])))
        cb=sum(a["branches"] for a in my_accs if any(n["member_id"]==active["id"] and days_since(n["date"])<=30 for n in a.get("notes",[])))
        week_calls=sum(1 for l in logs if days_since(l["date"])<=7)
    else:
        total=len(accounts); tb=sum(a["branches"] for a in accounts) or 1
        c30=sum(1 for a in accounts if days_since(a["last_call_date"])<=30)
        cb=sum(a["branches"] for a in accounts if days_since(a["last_call_date"])<=30)
        week_calls=None

    cov=round(c30/total*100) if total else 0
    br=round(cb/tb*100) if tb else 0

    col1,col2,col3,col4=st.columns(4)
    col1.metric("Coverage (30d)",f"{cov}%",f"{c30}/{total}")
    if is_rep: col2.metric("My calls this week",week_calls,f"{len(logs)} total")
    else: col2.metric("Overdue >14d",sum(1 for a in accounts if days_since(a["last_call_date"])>14),"need contact")
    col3.metric("Total branches",f"{tb:,}","under management")
    col4.metric("Branch coverage",f"{br}%",f"{cb:,} contacted")

    st.markdown("---")
    render_chart(logs,is_rep,active)
    st.markdown("---")

    if not is_rep:
        st.subheader("Top priority — overdue accounts")
        urgency=sorted([a for a in accounts if days_since(a["last_call_date"])>14],key=lambda x:days_since(x["last_call_date"]),reverse=True)[:5]
        if not urgency: st.success("All accounts contacted in the last 14 days.")
        for acc in urgency:
            d=days_since(acc["last_call_date"])
            c1,c2,c3=st.columns([3,1,1])
            c1.markdown(f"**{acc['brand_name']}** <small style='color:#888'>{acc['account_name']} · {acc['branches']} branches</small>",unsafe_allow_html=True)
            c2.markdown(urgency_badge(d),unsafe_allow_html=True)
            if has_perm(active["role"],"log"):
                if c3.button("Log call",key=f"dash_log_{acc['id']}"):
                    st.session_state.log_target=acc["id"]; st.session_state.show_log_modal=True; st.rerun()

# ── Chart ──────────────────────────────────────────────────────────────────────
def render_chart(logs,is_rep,active):
    st.subheader("Call activity")
    c1,c2,c3,c4=st.columns(4)
    gran=c1.selectbox("Granularity",["Daily","Weekly","Monthly","Yearly"],index=1,key="gran")
    ctype=c2.selectbox("Chart type",CHART_TYPES,key="ctype")
    offset=c3.number_input("Periods back",min_value=0,max_value=24,value=0,step=1,key="coffset")
    show_all=c4.checkbox("All team",value=not is_rep,disabled=is_rep,key="chart_all")

    users=st.session_state.users
    visible=[u for u in users if not is_rep or u["id"]==active["id"]] if not show_all else users
    today=date.today()

    if gran=="Daily":
        size=14
        periods=[str(today-timedelta(days=i+offset*size)) for i in range(size-1,-1,-1)]
        labels=[(today-timedelta(days=i+offset*size)).strftime("%d/%m") for i in range(size-1,-1,-1)]
        def bkt(d): return d[:10]
    elif gran=="Weekly":
        size=8
        def ws(d):
            if isinstance(d,str): d=datetime.strptime(d,"%Y-%m-%d").date()
            return str(d-timedelta(days=d.weekday()))
        raw=[]
        for i in range(size-1,-1,-1):
            raw.append(ws(today-timedelta(weeks=i+offset*size)))
        periods=list(dict.fromkeys(raw))
        labels=[datetime.strptime(p,"%Y-%m-%d").strftime("%b %d") for p in periods]
        def bkt(d): return ws(d[:10])
    elif gran=="Monthly":
        size=12
        periods=[]
        for i in range(size-1,-1,-1):
            m=today.month-i-offset*size; y=today.year+(m-1)//12; m=((m-1)%12)+1
            periods.append(f"{y}-{str(m).zfill(2)}")
        labels=[datetime.strptime(p+"-01","%Y-%m-%d").strftime("%b %Y") for p in periods]
        def bkt(d): return d[:7]
    else:
        size=4
        periods=[str(today.year-i-offset*size) for i in range(size-1,-1,-1)]
        labels=periods[:]
        def bkt(d): return d[:4]

    rows=[]
    for u in visible:
        for p,lbl in zip(periods,labels):
            cnt=sum(1 for l in logs if bkt(l["date"])==p and l["member_id"]==u["id"])
            rows.append({"Period":lbl,"User":u["name"].split()[0],"Calls":cnt,"Color":u["color"]})
    df=pd.DataFrame(rows)

    if df.empty or df["Calls"].sum()==0:
        st.info("No call data for this period."); return

    cmap={u["name"].split()[0]:u["color"] for u in visible}
    ct=ctype

    if ct=="Bar":
        fig=px.bar(df,x="Period",y="Calls",color="User",color_discrete_map=cmap,barmode="group")
    elif ct=="Stacked Bar":
        fig=px.bar(df,x="Period",y="Calls",color="User",color_discrete_map=cmap,barmode="stack")
    elif ct=="Line":
        fig=px.line(df,x="Period",y="Calls",color="User",color_discrete_map=cmap,markers=True)
    elif ct=="Area":
        fig=px.area(df,x="Period",y="Calls",color="User",color_discrete_map=cmap)
    elif ct=="Horizontal Bar":
        fig=px.bar(df,y="Period",x="Calls",color="User",color_discrete_map=cmap,barmode="stack",orientation="h")
    elif ct=="Pie":
        dfa=df.groupby("User")["Calls"].sum().reset_index()
        fig=px.pie(dfa,values="Calls",names="User",color="User",color_discrete_map=cmap)
    elif ct=="Donut":
        dfa=df.groupby("User")["Calls"].sum().reset_index()
        fig=px.pie(dfa,values="Calls",names="User",color="User",color_discrete_map=cmap,hole=0.4)
    else:
        fig=px.scatter(df,x="Period",y="Calls",color="User",color_discrete_map=cmap,size="Calls",size_max=18)

    fig.update_layout(height=300,margin=dict(l=10,r=10,t=20,b=10),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(0,0,0,0.06)"))
    st.plotly_chart(fig,use_container_width=True)

# ── Accounts ───────────────────────────────────────────────────────────────────
def render_accounts(active,is_rep):
    is_admin=has_perm(active["role"],"add_account")
    st.subheader("My accounts" if is_rep else "All accounts")

    col1,col2,col3=st.columns([3,2,2])
    search=col1.text_input("Search",placeholder="Name, brand or ID…",label_visibility="collapsed",key="acc_search")
    sort_by=col2.selectbox("Sort",["last_call_date","account_name","brand_name","branches"],label_visibility="collapsed",key="sort_by")
    sort_asc=col3.selectbox("Order",["Ascending","Descending"],label_visibility="collapsed",key="sort_dir")=="Ascending"

    accs=st.session_state.accounts
    if is_rep: accs=[a for a in accs if any(n["member_id"]==active["id"] for n in a.get("notes",[]))]
    if search:
        q=search.lower()
        accs=[a for a in accs if q in a["account_name"].lower() or q in a["brand_name"].lower() or q in a["id"].lower()]
    accs=sorted(accs,key=lambda x:str(x.get(sort_by,"")),reverse=not sort_asc)
    st.caption(f"{len(accs)} accounts")

    for acc in accs:
        d=days_since(acc["last_call_date"])
        last_note=acc["notes"][0] if acc.get("notes") else None
        last_by="—"
        if last_note:
            u=get_user(last_note.get("member_id",""))
            if u: last_by=u["name"].split()[0]

        with st.expander(f"**{acc['brand_name']}** · {acc['account_name']} · {acc['branches']} branches",expanded=False):
            c1,c2,c3,c4=st.columns(4)
            c1.markdown(f"**ID:** `{acc['id']}`")
            c2.markdown(f"**Sector:** {acc['sector']}")
            c3.markdown(f"**Contact:** {acc.get('contact_person','—')}")
            c4.markdown(f"**Last call:** {acc['last_call_date']}")
            st.markdown(f"**Status:** "+urgency_badge(d)+f" &emsp; **Last by:** {last_by}",unsafe_allow_html=True)

            for f in st.session_state.account_extra_fields:
                val=acc.get("extra_fields",{}).get(f["id"],"")
                if val: st.markdown(f"**{f['label']}:** {val}")

            if acc.get("notes"):
                st.markdown("**Recent interactions:**")
                for note in acc["notes"][:3]:
                    u=get_user(note.get("member_id",""))
                    s=get_status(note.get("status_id",""))
                    uname=u["name"].split()[0] if u else "—"
                    slabel=s["label"] if s else ""
                    st.markdown(f"&nbsp;&nbsp;`{note['date']}` **{uname}** {slabel}"+(f" — {note['text']}" if note.get("text") else ""))

            btn_cols=st.columns(4)
            if has_perm(active["role"],"log"):
                if btn_cols[0].button("Log call",key=f"acc_log_{acc['id']}"):
                    st.session_state.log_target=acc["id"]; st.session_state.show_log_modal=True; st.rerun()
            if is_admin:
                if btn_cols[1].button("Edit",key=f"acc_edit_{acc['id']}"):
                    st.session_state.editing_account=acc["id"]; st.rerun()
                if btn_cols[2].button("Delete",key=f"acc_del_{acc['id']}"):
                    st.session_state.accounts=[a for a in st.session_state.accounts if a["id"]!=acc["id"]]
                    st.success(f"Account '{acc['brand_name']}' deleted."); st.rerun()

    # Edit account inline
    if st.session_state.get("editing_account"):
        acc_id=st.session_state.editing_account
        acc=next((a for a in st.session_state.accounts if a["id"]==acc_id),None)
        if acc:
            st.markdown("---")
            st.subheader(f"Edit account — {acc['brand_name']}")
            with st.form(f"edit_acc_form_{acc_id}"):
                c1,c2=st.columns(2)
                new_name=c1.text_input("Account name",value=acc["account_name"])
                new_brand=c2.text_input("Brand name",value=acc["brand_name"])
                c3,c4=st.columns(2)
                new_branches=c3.number_input("# of branches",min_value=1,value=int(acc["branches"]))
                sector_idx=SECTORS.index(acc["sector"]) if acc["sector"] in SECTORS else 0
                new_sector=c4.selectbox("Sector",SECTORS,index=sector_idx)
                new_contact=st.text_input("Contact person",value=acc.get("contact_person",""))
                ef_vals={}
                for f in st.session_state.account_extra_fields:
                    cur=acc.get("extra_fields",{}).get(f["id"],"")
                    if f["type"]=="select":
                        opts=[""]+(f["options"] or [])
                        idx2=opts.index(cur) if cur in opts else 0
                        ef_vals[f["id"]]=st.selectbox(f["label"],opts,index=idx2,key=f"ef_{acc_id}_{f['id']}")
                    else:
                        ef_vals[f["id"]]=st.text_input(f["label"],value=cur,key=f"ef_{acc_id}_{f['id']}")
                s1,s2=st.columns(2)
                save=s1.form_submit_button("Save changes",type="primary")
                cancel=s2.form_submit_button("Cancel")
            if save:
                for i,a in enumerate(st.session_state.accounts):
                    if a["id"]==acc_id:
                        st.session_state.accounts[i]={**a,"account_name":new_name,"brand_name":new_brand,"branches":int(new_branches),"sector":new_sector,"contact_person":new_contact,"extra_fields":ef_vals}
                        break
                del st.session_state["editing_account"]; st.success("Account updated."); st.rerun()
            if cancel:
                del st.session_state["editing_account"]; st.rerun()

# ── Urgency ────────────────────────────────────────────────────────────────────
def render_urgency(active):
    st.subheader("Accounts not contacted in 14+ days")
    urgency=sorted([a for a in st.session_state.accounts if days_since(a["last_call_date"])>14],key=lambda x:days_since(x["last_call_date"]),reverse=True)
    st.caption(f"{len(urgency)} overdue")
    if not urgency: st.success("All accounts contacted recently."); return
    for acc in urgency:
        d=days_since(acc["last_call_date"])
        c1,c2,c3,c4=st.columns([2,2,1,1])
        c1.markdown(f"**{acc['brand_name']}** `{acc['id']}`")
        c2.markdown(f"<small>{acc['account_name']} · {acc['branches']} branches</small>",unsafe_allow_html=True)
        c3.markdown(urgency_badge(d),unsafe_allow_html=True)
        if has_perm(active["role"],"log"):
            if c4.button("Log call",key=f"urg_{acc['id']}"):
                st.session_state.log_target=acc["id"]; st.session_state.show_log_modal=True; st.rerun()
        st.divider()

# ── Activity Log ───────────────────────────────────────────────────────────────
def render_log(active,is_rep):
    st.subheader("My interaction log" if is_rep else "Interaction log")
    logs=get_all_logs(user_id=active["id"] if is_rep else None)
    st.caption(f"{len(logs)} entries")
    if not logs: st.info("No interactions logged yet."); return

    rows=[]
    for l in logs:
        u=get_user(l.get("member_id",""))
        s=get_status(l.get("status_id",""))
        ef=l.get("extra_fields",{})
        row={"Date":l["date"],"Brand":l["brand_name"],"Account":l["account_name"],"Team Member":u["name"] if u else "—","Status":s["label"] if s else "—","Notes":l.get("text","")}
        for f in st.session_state.call_extra_fields:
            row[f["label"]]=ef.get(f["id"],"")
        rows.append(row)
    df=pd.DataFrame(rows)
    st.dataframe(df,use_container_width=True,hide_index=True)
    if has_perm(active["role"],"export"):
        st.download_button("Export as CSV",df.to_csv(index=False).encode(),"activity_log.csv","text/csv")

# ── Users ──────────────────────────────────────────────────────────────────────
def render_users(active):
    is_admin=has_perm(active["role"],"manage_users")
    st.subheader("User management" if is_admin else "Team members")

    # ── Bulk CSV upload ──
    if is_admin:
        with st.expander("Bulk import users via CSV", expanded=False):
            template_df=pd.DataFrame(columns=["Name","Email","Role"])
            st.download_button("Download user template",template_df.to_csv(index=False).encode(),"users_template.csv","text/csv",key="dl_user_tmpl")
            up=st.file_uploader("Upload users CSV",type=["csv"],key="bulk_user_upload")
            if up:
                try:
                    df=pd.read_csv(up)
                    st.caption(f"{len(df)} rows detected")
                    st.dataframe(df.head(),use_container_width=True)
                    mode=st.radio("Mode",["Add new users","Update existing by email"],horizontal=True,key="bulk_user_mode")
                    if st.button("Import users",type="primary",key="do_bulk_user"):
                        added=updated=skipped=0
                        role_ids=[r["id"] for r in st.session_state.roles]
                        for _,row in df.iterrows():
                            name=str(row.get("Name","")).strip()
                            email=str(row.get("Email","")).strip()
                            role_val=str(row.get("Role","viewer")).strip().lower()
                            if not name or not email: skipped+=1; continue
                            if role_val not in role_ids: role_val="viewer"
                            existing=next((u for u in st.session_state.users if u["email"].lower()==email.lower()),None)
                            if existing and "Update" in mode:
                                existing["name"]=name; existing["role"]=role_val; updated+=1
                            elif not existing:
                                c=TEAM_COLORS[len(st.session_state.users)%len(TEAM_COLORS)]
                                st.session_state.users.append({"id":"u"+uid(),"name":name,"email":email,"role":role_val,**c})
                                added+=1
                            else: skipped+=1
                        st.success(f"Import complete: {added} added, {updated} updated, {skipped} skipped."); st.rerun()
                except Exception as ex:
                    st.error(f"CSV error: {ex}")

    # ── User list ──
    for u in st.session_state.users:
        c1,c2,c3=st.columns([3,1,2]) if is_admin else st.columns([4,1,1])
        c1.markdown(f"**{u['name']}** <small style='color:#888'>&nbsp;{u['email']}</small>",unsafe_allow_html=True)
        c2.markdown(role_badge_html(u["role"]),unsafe_allow_html=True)
        if is_admin:
            b1,b2,b3=c3.columns(3)
            if b1.button("Edit",key=f"eu_{u['id']}"):
                st.session_state.editing_user=u["id"]; st.rerun()
            if u["id"]!=active["id"] and b2.button("Delete",key=f"du_{u['id']}"):
                st.session_state.users=[x for x in st.session_state.users if x["id"]!=u["id"]]
                st.rerun()
        st.divider()

    if is_admin and st.button("+ Add user",type="primary",key="add_user_btn"):
        st.session_state.editing_user="__new__"; st.rerun()

    # ── Edit/Add user form ──
    if st.session_state.get("editing_user"):
        eid=st.session_state.editing_user
        existing=next((u for u in st.session_state.users if u["id"]==eid),None) if eid!="__new__" else None
        st.markdown("---")
        st.subheader("Edit user" if existing else "Add user")
        with st.form("user_form_main"):
            n_=st.text_input("Full name",value=existing["name"] if existing else "")
            e_=st.text_input("Email",value=existing["email"] if existing else "")
            role_ids=[r["id"] for r in st.session_state.roles]
            role_labels=[r["label"] for r in st.session_state.roles]
            cur_ridx=role_ids.index(existing["role"]) if existing and existing["role"] in role_ids else 2
            is_me=existing and existing["id"]==active["id"]
            if is_me:
                st.selectbox("Role",role_labels,index=cur_ridx,disabled=True)
                r_=existing["role"]
                st.caption("You cannot change your own role.")
            else:
                r_sel=st.selectbox("Role",role_labels,index=cur_ridx)
                r_=role_ids[role_labels.index(r_sel)]
            ef_={}
            for f in st.session_state.user_extra_fields:
                cur_v=existing.get("extra_fields",{}).get(f["id"],"") if existing else ""
                if f["type"]=="select":
                    ef_[f["id"]]=st.selectbox(f["label"],[""]+(f["options"] or []))
                else:
                    ef_[f["id"]]=st.text_input(f["label"],value=cur_v)
            sv,ca=st.columns(2)
            do_save=sv.form_submit_button("Save",type="primary")
            do_cancel=ca.form_submit_button("Cancel")
        if do_save and n_:
            c=TEAM_COLORS[len(st.session_state.users)%len(TEAM_COLORS)]
            new_u={"id":existing["id"] if existing else "u"+uid(),"name":n_,"email":e_,"role":r_,"extra_fields":ef_,**({"color":existing["color"],"bg":existing["bg"]} if existing else c)}
            if existing: st.session_state.users=[new_u if u["id"]==existing["id"] else u for u in st.session_state.users]
            else: st.session_state.users.append(new_u)
            del st.session_state["editing_user"]; st.rerun()
        if do_cancel:
            del st.session_state["editing_user"]; st.rerun()

# ── Field Builder & Roles ──────────────────────────────────────────────────────
def render_schema(active):
    tab1,tab2,tab3=st.tabs(["Custom Fields","Call Statuses","Role Manager"])

    # ── Custom Fields ──
    with tab1:
        st.subheader("Custom fields")
        all_fields=([(f,"Account") for f in st.session_state.account_extra_fields]+
                    [(f,"User")    for f in st.session_state.user_extra_fields]+
                    [(f,"Call")    for f in st.session_state.call_extra_fields])

        if not all_fields: st.caption("No custom fields yet.")
        for f,ent in all_fields:
            c1,c2,c3,c4,c5=st.columns([2,1,1,2,1])
            c1.markdown(f"**{f['label']}**")
            c2.markdown(f"`{f['type']}`")
            c3.markdown(f'<span class="badge-info">{ent}</span>',unsafe_allow_html=True)
            c4.markdown(", ".join(f.get("options",[])[:4]) if f.get("options") else "—")
            if c5.button("Remove",key=f"df_{f['id']}"):
                if ent=="Account": st.session_state.account_extra_fields=[x for x in st.session_state.account_extra_fields if x["id"]!=f["id"]]
                elif ent=="User": st.session_state.user_extra_fields=[x for x in st.session_state.user_extra_fields if x["id"]!=f["id"]]
                else: st.session_state.call_extra_fields=[x for x in st.session_state.call_extra_fields if x["id"]!=f["id"]]
                st.rerun()

        st.markdown("---")
        st.markdown("**Add new field**")
        with st.form("add_field"):
            fc1,fc2,fc3=st.columns(3)
            lbl=fc1.text_input("Label",placeholder="Field label")
            ftype=fc2.selectbox("Type",["text","number","date","select"])
            fent=fc3.selectbox("Applies to",["Account","User","Call"])
            opts_str=""
            if ftype=="select": opts_str=st.text_input("Options (comma-separated)",placeholder="High,Medium,Low")
            if st.form_submit_button("Add field",type="primary") and lbl:
                nf={"id":"f"+uid(),"label":lbl,"type":ftype,"options":[o.strip() for o in opts_str.split(",") if o.strip()]}
                if fent=="Account": st.session_state.account_extra_fields.append(nf)
                elif fent=="User": st.session_state.user_extra_fields.append(nf)
                else: st.session_state.call_extra_fields.append(nf)
                st.rerun()

    # ── Call Statuses ──
    with tab2:
        st.subheader("Call status options")
        for s in st.session_state.call_statuses:
            c1,c2,c3=st.columns([3,1,1])
            c1.markdown(f'<span style="display:inline-flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:{s["color"]};display:inline-block"></span>{s["label"]}</span>',unsafe_allow_html=True)
            if c2.button("Edit",key=f"es_{s['id']}"):
                st.session_state.editing_status=s["id"]; st.rerun()
            if c3.button("Remove",key=f"ds_{s['id']}"):
                st.session_state.call_statuses=[x for x in st.session_state.call_statuses if x["id"]!=s["id"]]; st.rerun()

        # Edit status
        if st.session_state.get("editing_status"):
            sid=st.session_state.editing_status
            st_obj=next((s for s in st.session_state.call_statuses if s["id"]==sid),None)
            if st_obj:
                st.markdown("---")
                with st.form("edit_status_form"):
                    new_lbl=st.text_input("Label",value=st_obj["label"])
                    new_col=st.color_picker("Color",value=st_obj["color"])
                    sv,ca=st.columns(2)
                    if sv.form_submit_button("Save",type="primary"):
                        st_obj["label"]=new_lbl; st_obj["color"]=new_col
                        del st.session_state["editing_status"]; st.rerun()
                    if ca.form_submit_button("Cancel"):
                        del st.session_state["editing_status"]; st.rerun()

        st.markdown("---")
        st.markdown("**Add status**")
        with st.form("add_status"):
            sc1,sc2=st.columns([3,1])
            new_slbl=sc1.text_input("Label",placeholder="Status label")
            new_scol=sc2.color_picker("Color","#378ADD")
            if st.form_submit_button("Add",type="primary") and new_slbl:
                st.session_state.call_statuses.append({"id":"cs"+uid(),"label":new_slbl,"color":new_scol}); st.rerun()

    # ── Role Manager ──
    with tab3:
        st.subheader("Role manager")
        st.caption("Add, edit, or delete roles and their permissions.")
        perm_keys=[k for k,_ in ALL_PERMS]
        perm_lbls={k:l for k,l in ALL_PERMS}
        PROTECTED={"admin","manager","rep","viewer"}

        for role in st.session_state.roles:
            with st.expander(f"**{role['label']}** ({role['id']})",expanded=False):
                c1,c2=st.columns([3,1])
                c1.markdown(role_badge_html(role["id"]),unsafe_allow_html=True)
                col_e,col_d=c2.columns(2)
                if col_e.button("Edit",key=f"er_{role['id']}"):
                    st.session_state.editing_role=role["id"]; st.rerun()
                if role["id"] not in PROTECTED:
                    if col_d.button("Delete",key=f"dr_{role['id']}"):
                        st.session_state.roles=[r for r in st.session_state.roles if r["id"]!=role["id"]]; st.rerun()
                st.markdown("**Permissions:**")
                perms_list=role.get("perms") or set()
                pc=st.columns(2)
                for i,(pk,pl) in enumerate(ALL_PERMS):
                    sym="✓" if pk in perms_list else "✕"
                    color="green" if pk in perms_list else "#aaa"
                    pc[i%2].markdown(f'<span style="color:{color}">{sym}</span> {pl}',unsafe_allow_html=True)

        if st.button("+ Add role",type="primary",key="add_role_btn"):
            st.session_state.editing_role="__new__"; st.rerun()

        # Edit/Add role form
        if st.session_state.get("editing_role"):
            eid=st.session_state.editing_role
            existing_role=next((r for r in st.session_state.roles if r["id"]==eid),None) if eid!="__new__" else None
            st.markdown("---")
            st.subheader("Edit role" if existing_role else "New role")
            with st.form("role_form"):
                if not existing_role or existing_role["id"] not in PROTECTED:
                    r_id=st.text_input("Role ID (no spaces, lowercase)",value=existing_role["id"] if existing_role else "",help="e.g. team_lead")
                else:
                    r_id=existing_role["id"]
                    st.text_input("Role ID (protected)",value=r_id,disabled=True)
                r_lbl=st.text_input("Display label",value=existing_role["label"] if existing_role else "")
                rc1,rc2=st.columns(2)
                r_color=rc1.color_picker("Text color",value=existing_role.get("color","#333333") if existing_role else "#333333")
                r_bg=rc2.color_picker("Badge background",value=existing_role.get("bg","#f0f0f0") if existing_role else "#f0f0f0")
                st.markdown("**Permissions**")
                cur_perms=existing_role.get("perms") or set() if existing_role else set()
                new_perms=set()
                for pk,pl in ALL_PERMS:
                    if st.checkbox(pl,value=pk in cur_perms,key=f"rp_{eid}_{pk}"):
                        new_perms.add(pk)
                sv,ca=st.columns(2)
                do_save=sv.form_submit_button("Save role",type="primary")
                do_cancel=ca.form_submit_button("Cancel")
            if do_save and r_id and r_lbl:
                r_id_clean=r_id.strip().lower().replace(" ","_")
                new_role={"id":r_id_clean,"label":r_lbl,"color":r_color,"bg":r_bg,"perms":new_perms}
                if existing_role:
                    st.session_state.roles=[new_role if r["id"]==existing_role["id"] else r for r in st.session_state.roles]
                else:
                    if any(r["id"]==r_id_clean for r in st.session_state.roles):
                        st.error("Role ID already exists.")
                    else:
                        st.session_state.roles.append(new_role)
                del st.session_state["editing_role"]; st.rerun()
            if do_cancel:
                del st.session_state["editing_role"]; st.rerun()

        # Permissions matrix
        st.markdown("---")
        st.markdown("**Permissions matrix**")
        mat={pl:{r["label"]:("✓" if pk in (r.get("perms") or set()) else "✕") for r in st.session_state.roles} for pk,pl in ALL_PERMS}
        st.dataframe(pd.DataFrame(mat).T,use_container_width=True)

# ── Log Call modal ─────────────────────────────────────────────────────────────
def render_log_modal(active):
    if not st.session_state.get("show_log_modal"): return
    acc=next((a for a in st.session_state.accounts if a["id"]==st.session_state.get("log_target")),None)
    if not acc: return

    st.markdown("---")
    st.subheader(f"Log interaction — {acc['brand_name']}")
    st.caption(f"{acc['account_name']} · {acc['branches']} branches · Last call: {acc['last_call_date']}")
    with st.form("log_form"):
        c1,c2=st.columns(2)
        names=[u["name"] for u in st.session_state.users]
        def_idx=next((i for i,u in enumerate(st.session_state.users) if u["id"]==active["id"]),0)
        member_name=c1.selectbox("Team member",names,index=def_idx)
        call_date=c2.date_input("Call date",value=date.today(),max_value=date.today())
        slabels=[s["label"] for s in st.session_state.call_statuses]
        status_lbl=st.selectbox("Call status",slabels if slabels else ["—"])
        ef_vals={}
        for f in st.session_state.call_extra_fields:
            if f["type"]=="select":
                ef_vals[f["id"]]=st.selectbox(f["label"],[""]+(f["options"] or []),key=f"lf_{f['id']}")
            else:
                ef_vals[f["id"]]=st.text_input(f["label"],placeholder=f["label"],key=f"lf_{f['id']}")
        notes_text=st.text_area("Notes",placeholder="Brief note…",height=80)
        s1,s2=st.columns(2)
        do_save=s1.form_submit_button("Save log",type="primary")
        do_cancel=s2.form_submit_button("Cancel")

    if do_save:
        member=next((u for u in st.session_state.users if u["name"]==member_name),None)
        status=next((s for s in st.session_state.call_statuses if s["label"]==status_lbl),None)
        new_note={"date":str(call_date),"text":notes_text,"member_id":member["id"] if member else "","status_id":status["id"] if status else "","extra_fields":ef_vals}
        for a in st.session_state.accounts:
            if a["id"]==acc["id"]:
                a["notes"].insert(0,new_note); a["last_call_date"]=str(call_date); break
        st.session_state.show_log_modal=False; st.session_state.log_target=None
        st.success(f"Call logged for {acc['brand_name']}"); st.rerun()
    if do_cancel:
        st.session_state.show_log_modal=False; st.session_state.log_target=None; st.rerun()

# ── Add Account form ───────────────────────────────────────────────────────────
def render_add_account(active):
    if not st.session_state.get("show_add_account"): return
    st.markdown("---")
    st.subheader("Add new account")
    with st.form("add_acc_form"):
        c1,c2=st.columns(2)
        acc_name=c1.text_input("Account name",placeholder="Legal entity name")
        brand=c2.text_input("Brand name",placeholder="Public-facing name")
        c3,c4=st.columns(2)
        branches=c3.number_input("# of branches",min_value=1,value=10)
        sector=c4.selectbox("Sector",SECTORS)
        contact=st.text_input("Contact person")
        ef_vals={}
        for f in st.session_state.account_extra_fields:
            if f["type"]=="select": ef_vals[f["id"]]=st.selectbox(f["label"],[""]+(f["options"] or []))
            else: ef_vals[f["id"]]=st.text_input(f["label"])
        s1,s2=st.columns(2)
        do_save=s1.form_submit_button("Add account",type="primary")
        do_cancel=s2.form_submit_button("Cancel")
    if do_save and acc_name and brand:
        new_acc={"id":gen_id("ACC",st.session_state.accounts),"account_name":acc_name,"brand_name":brand,"branches":int(branches),"sector":sector,"last_call_date":rnd_date(1),"contact_person":contact,"notes":[],"extra_fields":ef_vals}
        st.session_state.accounts.append(new_acc)
        st.session_state.show_add_account=False; st.success(f"Account '{brand}' added."); st.rerun()
    if do_cancel:
        st.session_state.show_add_account=False; st.rerun()

# ── Import CSV ─────────────────────────────────────────────────────────────────
def render_import():
    if not st.session_state.get("show_import"): return
    st.markdown("---")
    st.subheader("Import accounts — CSV")

    # Template download
    cols_needed=["Account ID","Account Name","Brand Name","# of Branches","Sector","Contact Person"]
    for f in st.session_state.account_extra_fields: cols_needed.append(f["label"])
    template_df=pd.DataFrame(columns=cols_needed)
    st.download_button("Download CSV template",template_df.to_csv(index=False).encode(),"accounts_template.csv","text/csv",key="dl_acc_tmpl")

    mode=st.radio("Import mode",["Add new rows","Update existing by Account ID","Add new + update existing"],horizontal=True,key="import_mode")
    uploaded=st.file_uploader("Upload CSV",type=["csv"],key="acc_csv_upload")

    if uploaded is not None:
        try:
            df=pd.read_csv(uploaded)
            # normalise column names — strip whitespace
            df.columns=[c.strip() for c in df.columns]
            st.caption(f"{len(df)} rows detected · Columns: {', '.join(df.columns)}")
            st.dataframe(df.head(6),use_container_width=True)

            if st.button("Confirm import",type="primary",key="confirm_import"):
                added=updated=skipped=0
                for _,row in df.iterrows():
                    acc_name=str(row.get("Account Name","")).strip()
                    brand_name=str(row.get("Brand Name","")).strip()
                    if not acc_name or not brand_name: skipped+=1; continue

                    branches_raw=row.get("# of Branches",0)
                    try: branches=int(float(str(branches_raw))) if str(branches_raw).strip() not in ("","nan") else 0
                    except: branches=0

                    acc_id_raw=str(row.get("Account ID","")).strip()
                    existing=next((a for a in st.session_state.accounts if a["id"]==acc_id_raw),None) if acc_id_raw and acc_id_raw.lower()!="nan" else None

                    new_acc={
                        "id": existing["id"] if existing else (acc_id_raw if acc_id_raw and acc_id_raw.lower()!="nan" else gen_id("ACC",st.session_state.accounts)),
                        "account_name": acc_name,
                        "brand_name": brand_name,
                        "branches": branches,
                        "sector": str(row.get("Sector","Retail")).strip() or "Retail",
                        "contact_person": str(row.get("Contact Person","")).strip(),
                        "last_call_date": str(row.get("Last Call Date",rnd_date(1))).strip() or rnd_date(1),
                        "notes": existing["notes"] if existing else [],
                        "extra_fields": {f["id"]: str(row.get(f["label"],"")).strip() for f in st.session_state.account_extra_fields},
                    }

                    if existing and "Update" in mode:
                        idx=st.session_state.accounts.index(existing)
                        st.session_state.accounts[idx]=new_acc; updated+=1
                    elif not existing:
                        st.session_state.accounts.append(new_acc); added+=1
                    else:
                        skipped+=1

                st.session_state.show_import=False
                st.success(f"Import complete — {added} added · {updated} updated · {skipped} skipped"); st.rerun()
        except Exception as ex:
            st.error(f"Failed to read CSV: {ex}")

    if st.button("Close import",key="close_import"):
        st.session_state.show_import=False; st.rerun()

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    init_state()
    active=get_active_user()
    is_rep=active["role"]=="rep"

    render_sidebar()

    # Top bar
    tc=st.columns([4,1,1])
    tc[0].title("Client Interaction Management")
    with tc[1]:
        if has_perm(active["role"],"import") and st.button("Import CSV",use_container_width=True,key="top_import"):
            st.session_state.show_import=True
            st.session_state.show_add_account=False
            st.session_state.show_log_modal=False
    with tc[2]:
        if has_perm(active["role"],"add_account") and st.button("+ Account",type="primary",use_container_width=True,key="top_add"):
            st.session_state.show_add_account=True
            st.session_state.show_import=False
            st.session_state.show_log_modal=False

    render_add_account(active)
    render_import()
    render_log_modal(active)

    urgency_count=sum(1 for a in st.session_state.accounts if days_since(a["last_call_date"])>14)
    tab_labels=["Dashboard","Accounts",f"Urgency ({urgency_count})","Activity Log","Users"]
    if has_perm(active["role"],"manage_schema"):
        tab_labels.append("Field Builder & Roles")

    tabs=st.tabs(tab_labels)
    with tabs[0]: render_dashboard(active,is_rep)
    with tabs[1]: render_accounts(active,is_rep)
    with tabs[2]: render_urgency(active)
    with tabs[3]: render_log(active,is_rep)
    with tabs[4]: render_users(active)
    if has_perm(active["role"],"manage_schema") and len(tabs)>5:
        with tabs[5]: render_schema(active)

if __name__=="__main__":
    main()
