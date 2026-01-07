import time
import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client

from api.client import API_URL

# --- 1. CONFIGURATION ---
SUPABASE_URL = "https://hmouoztlgrsotauzohgm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhtb3VvenRsZ3Jzb3RhdXpvaGdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzMjgwNjUsImV4cCI6MjA3OTkwNDA2NX0.7lICVEIkYaG_629xN_nVPUJspUgkhRswkKJKTF2TNBg"


@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Database: {e}")
        return None


supabase = init_supabase()

st.set_page_config(page_title="CodeImpact AI", page_icon="🎓", layout="wide")

# --- 2. CSS STYLES ---
st.markdown("""
<style>
    /* Removed max-width restriction to use full page width */
    .role-card {
        background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;
        text-align: center; height: 200px; display: flex; flex-direction: column;
        justify-content: center; align-items: center; cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .role-card:hover { border-color: #4CAF50; transform: translateY(-3px); }
    .metric-card {
        background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center;
    }
    .rubric-header { font-weight: bold; font-size: 1.1em; margin-top: 10px; color: #333; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "page" not in st.session_state: st.session_state.page = "home"
if "auth_user" not in st.session_state: st.session_state.auth_user = None


def navigate(page):
    st.session_state.page = page
    st.rerun()


def logout():
    st.session_state.auth_user = None
    navigate("home")


# ==========================================
# PAGE: HOME
# ==========================================
if st.session_state.page == "home":
    st.markdown("<h1 style='text-align: center;'>CodeImpact AI 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Where Code Meets Social Impact</h3>",
                unsafe_allow_html=True)
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="role-card"><h1>👨‍🎓</h1><h3>Student</h3><p>Submit projects</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Student Login", width='stretch'):
            st.session_state.target = "student"
            navigate("login")
    with c2:
        st.markdown("""<div class="role-card"><h1>🏫</h1><h3>Teacher</h3><p>Manage grading</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Teacher Login", width='stretch'):
            st.session_state.target = "teacher"
            navigate("login")
    with c3:
        st.markdown("""<div class="role-card"><h1>🛡️</h1><h3>Admin</h3><p>System logs</p></div>""",
                    unsafe_allow_html=True)
        if st.button("Admin Login", width='stretch'):
            st.session_state.target = "admin"
            navigate("login")

# ==========================================
# PAGE: LOGIN
# ==========================================
elif st.session_state.page == "login":
    tgt = st.session_state.target
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login"):
            st.markdown(f"<h3 style='text-align: center;'>{tgt.capitalize()} Login</h3>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            class_input = ""
            if tgt == "student":
                class_input = st.text_input("Class Name (e.g. Class 5A)")

            if st.form_submit_button("Sign In", width='stretch'):
                # 1. Fetch all users
                res = supabase.table("users").select("*").execute()
                found_user = None
                clean_u = u.strip().lower()

                if res.data:
                    for user in res.data:
                        if user["username"].strip().lower() == clean_u:
                            found_user = user
                            break

                if found_user:
                    if str(found_user["password"]) == p.strip():
                        if found_user["role"] != tgt:
                            st.error(f"User found, but is not a {tgt}.")
                        elif tgt == "student" and found_user.get("class_name") != class_input.strip():
                            st.error(f"You are registered in '{found_user.get('class_name')}', not '{class_input}'.")
                        else:
                            st.session_state.auth_user = found_user
                            st.success("Success!")
                            time.sleep(0.5)
                            navigate("dashboard")
                    else:
                        st.error("Invalid Password")
                else:
                    if tgt == "student" and class_input:
                        class_check = supabase.table("assignments").select("id").eq("class_name", class_input.strip()).execute()
                        if class_check.data and len(class_check.data) > 0:
                            new_student_data = {
                                "username": u.strip(),
                                "password": p.strip(),
                                "role": "student",
                                "full_name": u.strip(),
                                "class_name": class_input.strip()
                            }
                            try:
                                create_res = supabase.table("users").insert(new_student_data).execute()
                                if create_res.data:
                                    st.session_state.auth_user = create_res.data[0]
                                    st.success(f"Account created for class '{class_input.strip()}'! Logging in...")
                                    time.sleep(1)
                                    navigate("dashboard")
                                else:
                                    st.error("Failed to auto-create account.")
                            except Exception as e:
                                st.error(f"Error creating account: {e}")
                        else:
                            st.error(f"Class '{class_input}' does not exist (no assignments found). Please contact your teacher.")
                    else:
                        st.error("User not found")

    if st.button("Back"): navigate("home")

# ==========================================
# PAGE: DASHBOARD
# ==========================================
elif st.session_state.page == "dashboard":
    user = st.session_state.auth_user
    role = user["role"]

    st.sidebar.title(f"👤 {user.get('full_name', user['username'])}")
    st.sidebar.write(f"Role: {role.capitalize()}")
    if role == "student":
        st.sidebar.write(f"Class: {user.get('class_name')}")
    if st.sidebar.button("Logout"): logout()

    # --- STUDENT VIEW ---
    if role == "student":
        st.title("My Assignments")
        assigns = supabase.table("assignments").select("*").eq("class_name", user['class_name']).execute().data
        subs = supabase.table("submissions").select("*").eq("student_id", user['id']).execute().data
        sub_map = {s['assignment_id']: s for s in subs}

        if not assigns:
            st.info("No assignments found for your class.")

        for a in assigns:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(a['title'])

                my_sub = sub_map.get(a['id'])
                if my_sub:
                    status = my_sub['status']
                    c1.write(f"**Status:** {status}")
                    c1.write(f"**Link:** {my_sub['link']}")
                    if status == "Graded":
                        c1.success(f"Feedback: {my_sub.get('feedback')}")
                        c2.metric("Score", my_sub.get('final_score'))
                    else:
                        c2.info("Pending")
                else:
                    c1.warning("Not Submitted")
                    with c2.popover("Submit Now"):
                        link = st.text_input("Project Link", key=a['id'])
                        if st.button("Submit", key=f"btn_{a['id']}"):
                            supabase.table("submissions").insert({
                                "student_id": user['id'],
                                "assignment_id": a['id'],
                                "link": link,
                                "status": "Pending"
                            }).execute()
                            st.success("Submitted!")
                            st.rerun()

    # --- TEACHER VIEW ---
    elif role == "teacher":
        st.title("Teacher Dashboard")
        tab1, tab2 = st.tabs(["Grading", "Create Assignment (Rubrics)"])

        # Fetch commonly used data
        all_assigns_data = supabase.table("assignments").select("*").execute().data
        all_assigns_map = {a['id']: a for a in all_assigns_data}

        with tab1:
            st.subheader("Student Submissions")
            all_subs = supabase.table("submissions").select("*").execute().data
            all_users = {u['id']: u['full_name'] for u in
                         supabase.table("users").select("id, full_name").execute().data}

            if not all_subs:
                st.info("No submissions yet.")

            pending_subs = [s for s in all_subs if s['status'] == 'Pending']
            graded_subs = [s for s in all_subs if s['status'] == 'Graded']

            st.markdown(f"**Pending:** {len(pending_subs)} | **Graded:** {len(graded_subs)}")

            for s in all_subs:
                s_name = all_users.get(s['student_id'], "Unknown Student")
                assign_details = all_assigns_map.get(s['assignment_id'], {})
                a_title = assign_details.get('title', "Unknown Assignment")
                rubric = assign_details.get("rubric", [])

                status_icon = "✅" if s['status'] == "Graded" else "Dg"
                with st.expander(f"{status_icon} {s_name} - {a_title}"):
                    st.write(f"**Project Link:** {s['link']}")

                    # --- NEW GRADING VIEW (NESTED) ---
                    if rubric:
                        st.info("📋 **Rubric Assessment**")
                        # Handle both flat list (old) and nested list (new)
                        is_nested = isinstance(rubric, list) and len(rubric) > 0 and isinstance(rubric[0], dict) and "sub_criteria" in rubric[0]

                        if is_nested:
                            for cat in rubric:
                                if isinstance(cat, dict):
                                    c_name = cat.get("name", "Unnamed Category")
                                    c_weight = cat.get("weight", 0)
                                    st.markdown(f"**{c_name} ({c_weight}%)**")

                                    subs = cat.get("sub_criteria", [])
                                    if subs:
                                        df = pd.DataFrame(subs)
                                        st.dataframe(df, hide_index=True, use_container_width=True)
                        else:
                            if isinstance(rubric, list):
                                rubric_df = pd.DataFrame(rubric)
                                st.dataframe(rubric_df, hide_index=True, width='stretch')
                    else:
                        st.warning("No rubric defined for this assignment.")

                    st.divider()

                    if s['status'] == "Graded":
                        st.write(f"**Final Score:** {s.get('final_score')}")
                        st.write(f"**Feedback:** {s.get('feedback')}")
                    else:
                        # AI Analysis Button
                        if st.button("🤖 Analyze with AI", key=f"ai_{s['id']}"):
                            with st.spinner("Analyzing project code..."):
                                try:
                                    res = requests.post(f"{API_URL}/teacher/analyze_ai", json={
                                        "project_url": s['link'],
                                        "rubric_id": s['assignment_id']
                                    }).json()
                                    if "error" in res:
                                        st.error(res["error"])
                                    else:
                                        st.session_state[f"score_{s['id']}"] = res["suggested_score"]
                                        st.session_state[f"feedback_{s['id']}"] = res["suggested_feedback"]
                                        st.success("AI Analysis Complete!")
                                except Exception as e:
                                    st.error(f"AI Error: {e}")

                        with st.form(f"grade_{s['id']}"):
                            def_score = st.session_state.get(f"score_{s['id']}", 0)
                            def_fb = st.session_state.get(f"feedback_{s['id']}", "")

                            score = st.number_input("Final Score", 0, 100, value=int(def_score), step=1)
                            fb = st.text_area("Feedback", value=def_fb, height=150)

                            if st.form_submit_button("Submit Grade"):
                                supabase.table("submissions").update({
                                    "final_score": score,
                                    "feedback": fb,
                                    "status": "Graded"
                                }).eq("id", s['id']).execute()
                                st.success("Graded Successfully!")
                                time.sleep(1)
                                st.rerun()

        with tab2:
            st.subheader("Manage Assignments (Hierarchical Rubric)")

            # Mode Selection
            mode = st.radio("Action", ["Create New Assignment"], horizontal=True)

            if mode == "Create New Assignment":
                title = st.text_input("Assignment Title")
                cls = st.text_input("Class Name")

                st.divider()
                st.write("### 🏗️ Rubric Structure")
                st.info("The 4 Main Categories are fixed. You can adjust the weights (must sum to 100%) and the sub-criteria within them.")

                # Fixed Categories
                default_cats = [
                    {"name": "Code & Algorithmics", "weight": 40, "subs": [
                        {"name": "Dr Scratch Score", "weight": 60},
                        {"name": "Amount of Objects", "weight": 10},
                        {"name": "Input Tools", "weight": 10},
                        {"name": "Events & Messages", "weight": 10},
                        {"name": "Self Learning", "weight": 10}
                    ]},
                    {"name": "Usability", "weight": 10, "subs": [
                        {"name": "Design & UX", "weight": 50},
                        {"name": "Multimedia", "weight": 50}
                    ]},
                    {"name": "Creativity", "weight": 30, "subs": [
                        {"name": "Innovation", "weight": 50},
                        {"name": "Simplicity", "weight": 20},
                        {"name": "Pedagogical Level", "weight": 30}
                    ]},
                    {"name": "Presentation & Other", "weight": 20, "subs": [
                        {"name": "Documentation", "weight": 50},
                        {"name": "Oral Presentation", "weight": 50}
                    ]}
                ]

                final_rubric_structure = []
                total_main_weight = 0

                cols = st.columns(4)
                for i in range(4):
                    with cols[i]:
                        # Fixed Name Display
                        cat_name = default_cats[i]["name"]
                        st.markdown(f"#### {cat_name}")

                        # Editable Weight - Updates on change now
                        c_weight = st.number_input(f"Weight %", min_value=0, max_value=100, value=default_cats[i]["weight"], key=f"w_{i}")
                        total_main_weight += c_weight

                        st.caption("Sub-Criteria")
                        # Editable Sub-Criteria
                        df_subs = pd.DataFrame(default_cats[i]["subs"])
                        edited_subs = st.data_editor(df_subs, num_rows="dynamic", key=f"sub_{i}", hide_index=True)

                        sub_sum = edited_subs["weight"].sum()
                        if sub_sum != 100:
                            st.error(f"Subs: {sub_sum}%")
                        else:
                            st.caption(f"Subs: 100% ✅")

                        final_rubric_structure.append({
                            "name": cat_name,
                            "weight": c_weight,
                            "sub_criteria": edited_subs.to_dict(orient="records")
                        })

                st.divider()
                # Validation Logic
                if total_main_weight != 100:
                    st.error(f"Total Main Weight is {total_main_weight}%. It must be exactly 100%.")
                else:
                    st.success(f"Total Main Weight: {total_main_weight}% ✅")

                # Action Button (Standard Button, not Form Submit)
                if st.button("Create Assignment"):
                    if total_main_weight != 100:
                        st.error("Please fix main category weights before creating.")
                    else:
                        supabase.table("assignments").insert({
                            "teacher_id": user['id'],
                            "title": title,
                            "class_name": cls,
                            "rubric": final_rubric_structure
                        }).execute()
                        st.success(f"Assignment '{title}' created with hierarchical rubric!")
                        time.sleep(2)
                        st.rerun()

    # --- ADMIN VIEW ---
    elif role == "admin":
        st.title("System Overview & Statistics")

        users_data = supabase.table("users").select("*").execute().data
        assignments_data = supabase.table("assignments").select("id").execute().data
        submissions_data = supabase.table("submissions").select("*").execute().data

        total_students = len([u for u in users_data if u['role'] == 'student'])
        total_teachers = len([u for u in users_data if u['role'] == 'teacher'])
        total_assigns = len(assignments_data)
        total_submissions = len(submissions_data)
        graded_count = len([s for s in submissions_data if s['status'] == 'Graded'])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Students", total_students)
        m2.metric("Teachers", total_teachers)
        m3.metric("Assignments", total_assigns)
        m4.metric("Submissions", total_submissions, f"{graded_count} Graded")

        st.divider()

        st.subheader("Add New User")
        with st.form("add_user_form"):
            c1, c2 = st.columns(2)
            new_u = c1.text_input("Username")
            new_p = c2.text_input("Password", type="password")
            new_name = c1.text_input("Full Name")
            new_role = c2.selectbox("Role", ["student", "teacher", "admin"])
            new_class = st.text_input("Class Name (for Students)") if new_role == "student" else ""

            if st.form_submit_button("Create User"):
                if not new_u or not new_p:
                    st.error("Username and Password are required.")
                else:
                    try:
                        user_data = {
                            "username": new_u,
                            "password": new_p,
                            "full_name": new_name,
                            "role": new_role,
                            "class_name": new_class if new_role == "student" else None
                        }
                        supabase.table("users").insert(user_data).execute()
                        st.success(f"User '{new_u}' ({new_role}) created successfully!")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating user: {e}")

        st.divider()
        st.subheader("Bulk Upload Users")

        try:
            template_text = requests.get(f"{API_URL}/admin/users/template").text
            st.download_button(
                label="Download CSV Template",
                data=template_text,
                file_name="users_template.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error("Could not fetch template from server.")

        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

        if uploaded_file is not None:
            if st.button("Process Upload"):
                with st.spinner("Uploading and creating users..."):
                    try:
                        res = requests.post(f"{API_URL}/admin/users/upload", files={"file": uploaded_file.getvalue()})

                        if res.status_code == 200:
                            data = res.json()
                            st.success(data["message"])
                            if data.get("errors"):
                                with st.expander("See Errors"):
                                    for err in data["errors"]:
                                        st.write(f"- {err}")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        st.subheader("User Database")
        st.dataframe(users_data)