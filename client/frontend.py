import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="CodeImpact AI", page_icon="🎓", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .block-container { max-width: 1000px; }
    .role-card {
        background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;
        text-align: center; height: 200px; display: flex; flex-direction: column;
        justify-content: center; align-items: center; cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .role-card:hover { border-color: #4CAF50; transform: translateY(-3px); }
    .status-graded { color: #2e7d32; font-weight: bold; }
    .status-pending { color: #f57c00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "page" not in st.session_state: st.session_state.page = "home"
if "auth_user" not in st.session_state: st.session_state.auth_user = None


def navigate(page):
    st.session_state.page = page
    st.rerun()


def logout():
    st.session_state.auth_user = None
    st.session_state.page = "home"
    st.rerun()


# ==========================================
# 1. HOME & LOGIN
# ==========================================
if st.session_state.page == "home":
    st.title("CodeImpact AI 🚀")
    st.subheader("Automated Scratch Project Evaluation")
    st.divider()

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown('<div class="role-card"><h2>👨‍🎓</h2><h3>Student</h3></div>', unsafe_allow_html=True)
        if st.button("Student Login"): st.session_state.target = "student"; navigate("login")
    with c2:
        st.markdown('<div class="role-card"><h2>👩‍🏫</h2><h3>Teacher</h3></div>', unsafe_allow_html=True)
        if st.button("Teacher Login"): st.session_state.target = "teacher"; navigate("login")
    with c3:
        st.markdown('<div class="role-card"><h2>🛡️</h2><h3>Admin</h3></div>', unsafe_allow_html=True)
        if st.button("Admin Login"): st.session_state.target = "admin"; navigate("login")

elif st.session_state.page == "login":
    tgt = st.session_state.target
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.info(f"💡 **Demo Creds:** User=`{tgt}` | Pass=`123`")
        with st.form("login"):
            st.write(f"### {tgt.capitalize()} Login")
            u = st.text_input("Name")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                try:
                    res = requests.post(f"{API_URL}/login", json={"username": u, "password": p})
                    if res.status_code == 200:
                        data = res.json()
                        if data['role'] == tgt:
                            st.session_state.auth_user = data
                            st.success("Success!")
                            time.sleep(0.5);
                            navigate("dashboard")
                        else:
                            st.error("Wrong Role")
                    else:
                        st.error("Invalid Credentials")
                except:
                    st.error("Backend Offline")
        if st.button("Back"): navigate("home")

# ==========================================
# 2. DASHBOARDS
# ==========================================
elif st.session_state.page == "dashboard":
    user = st.session_state.auth_user
    role = user['role']

    st.sidebar.header(f"👤 {user['name']}")
    st.sidebar.caption(f"ID: {user['id']} | Role: {role.upper()}")
    if st.sidebar.button("Logout"): logout()

    # --- STUDENT ---
    if role == "student":
        st.title("My Projects")
        with st.expander("📤 Upload New Project", expanded=True):
            t = st.text_input("Title")
            l = st.text_input("Scratch Link")
            if st.button("Submit"):
                requests.post(f"{API_URL}/student/submit", json={"student_id": user['id'], "title": t, "link": l})
                st.success("Submitted!");
                time.sleep(1);
                st.rerun()

        projs = requests.get(f"{API_URL}/student/{user['id']}/projects").json()
        for p in projs:
            with st.container(border=True):
                st.markdown(f"### {p['title']}")
                st.write(f"🔗 {p['link']}")
                if p['status'] == "Graded":
                    st.markdown(f"**Status:** :green[Graded] | **Score:** {p['score']}/100")
                    st.info(f"**Feedback:**\n\n{p['feedback']}")
                else:
                    st.markdown("**Status:** :orange[Pending Review]")

    # --- TEACHER ---
    elif role == "teacher":
        st.title("Teacher Workspace 🍎")
        menu = st.sidebar.radio("Navigate", ["Classroom", "Rubrics"])

        if menu == "Classroom":
            students = requests.get(f"{API_URL}/teacher/students").json()
            st.write("### Enrolled Students")
            cols = st.columns(3)
            for i, s in enumerate(students):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.write(f"**{s['name']}**")
                        st.caption(f"Projects: {s.get('project_count', 0)}")
                        if st.button("View & Grade", key=s['id']):
                            st.session_state.view_sid = s['id']
                            st.session_state.view_sname = s['name']
                            navigate("grading_list")

        elif menu == "Rubrics":
            st.write("### Rubric Manager")
            with st.form("new_rubric"):
                title = st.text_input("Rubric Title (e.g., 'Loops & Variables')")
                c1 = st.text_input("Criterion 1", "Code Efficiency");
                w1 = st.number_input("Weight %", 50, key="w1")
                c2 = st.text_input("Criterion 2", "Creativity");
                w2 = st.number_input("Weight %", 50, key="w2")
                if st.form_submit_button("Create Rubric"):
                    crit = [{"name": c1, "weight": w1}, {"name": c2, "weight": w2}]
                    requests.post(f"{API_URL}/teacher/rubrics",
                                  json={"teacher_id": 1, "title": title, "criteria": crit})
                    st.success("Rubric Created!")

            st.divider()
            st.write("Existing Rubrics:")
            rubs = requests.get(f"{API_URL}/teacher/rubrics").json()
            for r in rubs: st.write(f"- {r['title']}")

    # --- ADMIN ---
    elif role == "admin":
        st.title("Admin Console 🛡️")
        stats = requests.get(f"{API_URL}/admin/stats").json()

        # Stats Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Students", stats['students'])
        c2.metric("Teachers", stats['teachers'])
        c3.metric("Projects", stats['projects'])
        c4.metric("Graded", stats['graded'])

        st.divider()
        st.subheader("User Database")
        users = requests.get(f"{API_URL}/admin/users").json()
        st.table(users)

# ==========================================
# 3. GRADING FLOW (Teacher)
# ==========================================
elif st.session_state.page == "grading_list":
    st.button("← Back to Classroom", on_click=lambda: navigate("dashboard"))
    st.header(f"Projects by: {st.session_state.view_sname}")

    projs = requests.get(f"{API_URL}/teacher/student/{st.session_state.view_sid}/projects").json()
    if not projs: st.warning("No projects found.")

    for p in projs:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{p['title']}** ({p['link']})")
            if p['status'] == "Pending":
                if c2.button("Grade", key=p['id']):
                    st.session_state.grade_p = p
                    navigate("grading_screen")
            else:
                c2.success(f"Score: {p['score']}")

elif st.session_state.page == "grading_screen":
    p = st.session_state.grade_p
    st.button("Cancel", on_click=lambda: navigate("grading_list"))
    st.title(f"Grading: {p['title']}")

    # 1. Select Rubric
    rubrics = requests.get(f"{API_URL}/teacher/rubrics").json()
    if not rubrics: st.error("Please create a Rubric first."); st.stop()

    rub_opts = {r['title']: r['id'] for r in rubrics}
    sel_rub_name = st.selectbox("Select Grading Rubric", list(rub_opts.keys()))
    sel_rub_id = rub_opts[sel_rub_name]

    # 2. AI BUTTON
    st.info("🤖 **AI Assistant:** Click below to analyze the Scratch code automatically.")
    if st.button("✨ Run AI Analysis"):
        with st.spinner("AI is analyzing blocks, variables, and logic..."):
            ai_res = requests.post(f"{API_URL}/teacher/analyze_ai",
                                   json={"project_url": p['link'], "rubric_id": sel_rub_id}).json()
            st.session_state.ai_result = ai_res
            st.success("Analysis Complete!")

    # 3. Final Grading Form
    with st.form("final_grade"):
        # Pre-fill if AI ran
        default_score = st.session_state.get("ai_result", {}).get("suggested_score", 0)
        default_feedback = st.session_state.get("ai_result", {}).get("suggested_feedback", "")

        final_score = st.slider("Final Score", 0, 100, default_score)
        final_feedback = st.text_area("Feedback to Student", default_feedback, height=150)

        if st.form_submit_button("Submit Grade"):
            requests.post(f"{API_URL}/teacher/grade",
                          json={"project_id": p['id'], "rubric_id": sel_rub_id, "total_score": final_score,
                                "feedback": final_feedback, "details": {}})
            st.success("Grade Saved!")
            # Clear AI state
            if "ai_result" in st.session_state: del st.session_state.ai_result
            time.sleep(1)
            navigate("grading_list")