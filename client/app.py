import time

import pandas as pd
import streamlit as st
from supabase import create_client

# --- CONFIGURATION ---
# REPLACE THESE WITH YOUR REAL KEYS FROM SUPABASE DASHBOARD
SUPABASE_URL = "https://hmouoztlgrsotauzohgm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhtb3VvenRsZ3Jzb3RhdXpvaGdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzMjgwNjUsImV4cCI6MjA3OTkwNDA2NX0.7lICVEIkYaG_629xN_nVPUJspUgkhRswkKJKTF2TNBg"


@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None


supabase = init_supabase()

st.set_page_config(page_title="CodeImpact AI", page_icon="🎓", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .block-container { max-width: 1200px; padding-top: 2rem; }
    .role-card {
        background: white; padding: 30px; border-radius: 12px; border: 1px solid #ddd;
        text-align: center; height: 220px; display: flex; flex-direction: column;
        justify-content: center; align-items: center; cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: 0.3s;
    }
    .role-card:hover { border-color: #FF4B4B; transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
    .rubric-card { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 10px; }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
    .total-ok { color: green; font-weight: bold; }
    .total-bad { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "page" not in st.session_state: st.session_state.page = "home"
if "auth_user" not in st.session_state: st.session_state.auth_user = None


def navigate(page): st.session_state.page = page; st.rerun()


def logout(): st.session_state.auth_user = None; navigate("home")


# ==========================================
# SCREEN 1: HOME
# ==========================================
if st.session_state.page == "home":
    st.title("CodeImpact AI 🚀")
    st.write("### Select your role")
    st.divider()
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown('<div class="role-card"><h2>👨‍🎓</h2><h3>Student</h3></div>', unsafe_allow_html=True)
        if st.button("Student Login"): st.session_state.role = "student"; navigate("login")
    with c2:
        st.markdown('<div class="role-card"><h2>👩‍🏫</h2><h3>Teacher</h3></div>', unsafe_allow_html=True)
        if st.button("Teacher Login"): st.session_state.role = "teacher"; navigate("login")
    with c3:
        st.markdown('<div class="role-card"><h2>🛡️</h2><h3>Admin</h3></div>', unsafe_allow_html=True)
        if st.button("Admin Login"): st.session_state.role = "admin"; navigate("login")

# ==========================================
# SCREEN 2: LOGIN
# ==========================================
elif st.session_state.page == "login":
    role = st.session_state.role
    st.button("← Back", on_click=lambda: navigate("home"))

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader(f"{role.capitalize()} Login")
            name = st.text_input("Username")
            password = st.text_input("Password", type="password")

            class_name = None
            if role == "student":
                class_name = st.text_input("Class Name", placeholder="e.g. Class A")
                st.caption("ℹ️ New students: typing a valid class name will create your account.")

            if st.form_submit_button("Sign In"):
                if not name or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        # 1. SEARCH USER
                        res = supabase.table("users").select("*").eq("username", name).execute()

                        # A. USER EXISTS
                        if res.data:
                            user = res.data[0]
                            if user['password'] == password:
                                if user['role'] == role:
                                    st.session_state.auth_user = user
                                    navigate("dashboard")
                                else:
                                    st.error(f"Error: You are a {user['role']}, not a {role}.")
                            else:
                                st.error("Incorrect Password.")

                        # B. AUTO-REGISTER (Student Only)
                        elif role == "student":
                            if not class_name:
                                st.error("Class Name is required for new students.")
                            else:
                                class_check = supabase.table("assignments").select("*").eq("class_name",
                                                                                           class_name).execute()
                                if class_check.data:
                                    new_user = {
                                        "username": name, "password": password, "role": "student",
                                        "full_name": name, "class_name": class_name
                                    }
                                    reg = supabase.table("users").insert(new_user).execute()
                                    st.session_state.auth_user = reg.data[0]
                                    st.success("🎉 Registered & Logged In!")
                                    time.sleep(1);
                                    navigate("dashboard")
                                else:
                                    st.error(f"Class '{class_name}' does not exist.")

                        else:
                            st.error("Account not found. Contact Admin.")

                    except Exception as e:
                        st.error(f"Connection Error: {e}")

# ==========================================
# SCREEN 3: DASHBOARDS
# ==========================================
elif st.session_state.page == "dashboard":
    user = st.session_state.auth_user
    role = user['role']
    st.sidebar.title(f"👤 {user['full_name']}")
    if st.sidebar.button("Logout"): logout()

    # ---------------------------
    # STUDENT
    # ---------------------------
    if role == "student":
        st.title(f"Assignments: {user['class_name']}")
        assigns = supabase.table("assignments").select("*").eq("class_name", user['class_name']).execute().data

        if not assigns: st.info("No projects assigned yet.")

        for a in assigns:
            sub_res = supabase.table("submissions").select("*").eq("assignment_id", a['id']).eq("student_id",
                                                                                                user['id']).execute()
            sub = sub_res.data[0] if sub_res.data else None

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(a['title'])
                if sub:
                    if sub['status'] == "Graded":
                        c1.markdown(":green[**Graded**]")
                        c1.info(f"Feedback: {sub['feedback']}")
                        c2.metric("Score", f"{sub['final_score']}/100")
                    else:
                        c1.markdown(":orange[**Pending Review**]")
                        c1.caption(f"Link: {sub['link']}")
                else:
                    c1.markdown(":red[**Not Submitted**]")
                    with c1.expander("✋ Hand In Project"):
                        l = st.text_input("Paste Link", key=f"l_{a['id']}")
                        if st.button("Submit", key=f"b_{a['id']}"):
                            supabase.table("submissions").insert(
                                {"assignment_id": a['id'], "student_id": user['id'], "link": l}).execute()
                            st.rerun()

    # ---------------------------
    # TEACHER
    # ---------------------------
    elif role == "teacher":
        st.title("Teacher Dashboard 🍎")
        menu = st.sidebar.radio("Navigate", ["Create Class Project", "Grade Projects"])

        if menu == "Create Class Project":
            st.subheader("Create New Project")
            with st.container(border=True):
                c_name = st.text_input("Class Name", "Class A")
                p_title = st.text_input("Project Title")

                st.write("**Define 4 Grading Categories (100% Total)**")
                cats = []
                current_total = 0
                defaults = ["Logic", "Creativity", "Efficiency", "Functionality"]

                for i in range(4):
                    st.markdown(f"**Category {i + 1}**")
                    col_a, col_b = st.columns([2, 1])
                    name = col_a.text_input(f"Name", defaults[i], key=f"cn_{i}")
                    weight = col_b.number_input(f"Weight %", 0, 100, 25, key=f"cw_{i}")
                    checks = st.text_area(f"Checklist (comma separated)", "Item 1, Item 2, Item 3", key=f"cl_{i}",
                                          height=68)

                    cats.append({"name": name, "weight": weight,
                                 "checklist": [x.strip() for x in checks.split(",") if x.strip()]})
                    current_total += weight
                    st.divider()

                if current_total == 100:
                    st.markdown(f"<p class='total-ok'>Total: {current_total}% (Perfect)</p>", unsafe_allow_html=True)
                    if st.button("Publish Project"):
                        if c_name and p_title:
                            supabase.table("assignments").insert({
                                "teacher_id": user['id'], "class_name": c_name, "title": p_title, "rubric": cats
                            }).execute()
                            st.success(f"Published to {c_name}!")
                        else:
                            st.error("Missing Name or Title")
                else:
                    st.markdown(f"<p class='total-bad'>Total: {current_total}% (Fix to 100%)</p>",
                                unsafe_allow_html=True)

        elif menu == "Grade Projects":
            st.subheader("Grading Center")
            my_classes = supabase.table("assignments").select("class_name").eq("teacher_id", user['id']).execute().data
            unique_classes = list(set([c['class_name'] for c in my_classes]))

            if unique_classes:
                sel_class = st.selectbox("Select Class", unique_classes)
                class_projs = supabase.table("assignments").select("*").eq("class_name", sel_class).execute().data

                if class_projs:
                    p_map = {p['title']: p for p in class_projs}
                    sel_p_title = st.selectbox("Select Project", list(p_map.keys()))
                    sel_p = p_map[sel_p_title]

                    st.write("---")
                    subs = supabase.table("submissions").select("*, users(full_name)").eq("assignment_id",
                                                                                          sel_p['id']).execute().data

                    if not subs: st.info("No submissions yet.")

                    for s in subs:
                        status_icon = "🟢" if s['status'] == "Graded" else "🟠"
                        with st.expander(f"{status_icon} {s['users']['full_name']}"):
                            st.write(f"**Link:** {s['link']}")

                            with st.form(key=f"g_{s['id']}"):
                                st.write("### Rubric Assessment")
                                final_score = 0

                                for cat in sel_p['rubric']:
                                    st.markdown(
                                        f"<div class='rubric-card'><b>{cat['name']}</b> ({cat['weight']}%)</div>",
                                        unsafe_allow_html=True)
                                    checked = 0
                                    total_items = len(cat['checklist'])
                                    cols = st.columns(2)
                                    for idx, item in enumerate(cat['checklist']):
                                        if cols[idx % 2].checkbox(item, key=f"chk_{s['id']}_{cat['name']}_{idx}"):
                                            checked += 1

                                    if total_items > 0:
                                        cat_score = (checked / total_items) * cat['weight']
                                    else:
                                        cat_score = 0
                                    final_score += cat_score

                                st.markdown(f"#### Final Score: {int(final_score)}")
                                fb = st.text_area("Feedback", value=s.get('feedback') or "Good work!")

                                if st.form_submit_button("Submit Grade"):
                                    supabase.table("submissions").update({
                                        "status": "Graded", "final_score": int(final_score), "feedback": fb
                                    }).eq("id", s['id']).execute()
                                    st.success("Saved!")
                                    time.sleep(1);
                                    st.rerun()

    # ---------------------------
    # ADMIN (UPDATED WITH TABS)
    # ---------------------------
    elif role == "admin":
        st.title("Admin Console 🛡️")

        # TABS FOR ADMIN
        tab1, tab2 = st.tabs(["Manage Teachers", "Classes & Analytics"])

        # TAB 1: ADD TEACHER
        with tab1:
            st.subheader("Register New Teacher")
            with st.form("new_teacher"):
                st.write("Enter Teacher Details")
                n = st.text_input("Full Name")
                u = st.text_input("Username")
                p = st.text_input("Password")
                if st.form_submit_button("Create Account"):
                    if n and u and p:
                        supabase.table("users").insert(
                            {"role": "teacher", "full_name": n, "username": u, "password": p}).execute()
                        st.success(f"Teacher '{n}' added successfully!")
                    else:
                        st.error("Please fill all fields.")

            st.divider()
            st.write("### Existing Teachers")
            teachers = supabase.table("users").select("full_name, username").eq("role", "teacher").execute().data
            if teachers:
                st.table(teachers)
            else:
                st.info("No teachers found.")

        # TAB 2: SYSTEM OVERVIEW (GRADES & PROJECTS)
        with tab2:
            st.subheader("System Performance")

            # Fetch All Assignments (Projects)
            all_assigns = supabase.table("assignments").select("id, title, class_name, teacher_id").execute().data

            if all_assigns:
                data = []
                for assign in all_assigns:
                    # Fetch Teacher Name
                    teacher_res = supabase.table("users").select("full_name").eq("id", assign['teacher_id']).execute()
                    t_name = teacher_res.data[0]['full_name'] if teacher_res.data else "Unknown"

                    # Fetch Submissions for this assignment to calc stats
                    subs = supabase.table("submissions").select("final_score, status").eq("assignment_id",
                                                                                          assign['id']).execute().data

                    total_subs = len(subs)
                    graded_subs = len([s for s in subs if s['status'] == "Graded"])

                    # Calculate Average
                    scores = [s['final_score'] for s in subs if s['status'] == "Graded"]
                    avg_score = int(sum(scores) / len(scores)) if scores else 0

                    data.append({
                        "Class": assign['class_name'],
                        "Project": assign['title'],
                        "Teacher": t_name,
                        "Submissions": total_subs,
                        "Avg Grade": f"{avg_score}%" if graded_subs > 0 else "N/A"
                    })

                # Show Data Table
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)

                # High Level Metrics
                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Projects", len(all_assigns))
                m2.metric("Total Submissions", sum([d['Submissions'] for d in data]))

            else:
                st.info("No projects created in the system yet.")
