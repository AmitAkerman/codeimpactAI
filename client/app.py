import time
import streamlit as st
import pandas as pd
import requests
from supabase import create_client

from api.client import API_URL

# --- CONFIGURATION ---
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

st.markdown("""
<style>
    .role-card {
        background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;
        text-align: center; height: 200px; display: flex; flex-direction: column;
        justify-content: center; align-items: center; cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .role-card:hover { border-color: #4CAF50; transform: translateY(-3px); }
</style>
""", unsafe_allow_html=True)

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
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="role-card"><h1>👨‍🎓</h1><h3>Student</h3></div>""", unsafe_allow_html=True)
        if st.button("Student Login", width='stretch'):
            st.session_state.target = "student"
            navigate("login")
    with c2:
        st.markdown("""<div class="role-card"><h1>🏫</h1><h3>Teacher</h3></div>""", unsafe_allow_html=True)
        if st.button("Teacher Login", width='stretch'):
            st.session_state.target = "teacher"
            navigate("login")
    with c3:
        st.markdown("""<div class="role-card"><h1>🛡️</h1><h3>Admin</h3></div>""", unsafe_allow_html=True)
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
            if tgt == "student":
                st.caption("Tip: Your class name is loaded from your profile.")

            if st.form_submit_button("Sign In", width='stretch'):
                res = supabase.table("users").select("*").execute()
                found_user = None
                if res.data:
                    for user in res.data:
                        if user["username"].strip().lower() == u.strip().lower():
                            found_user = user
                            break
                if found_user and str(found_user["password"]) == p.strip():
                    st.session_state.auth_user = found_user
                    navigate("dashboard")
                else:
                    st.error("Invalid Credentials")
    if st.button("Back"): navigate("home")

# ==========================================
# PAGE: DASHBOARD
# ==========================================
elif st.session_state.page == "dashboard":
    user = st.session_state.auth_user
    role = user["role"]

    st.sidebar.title(f"👤 {user.get('full_name', user['username'])}")
    if st.sidebar.button("Logout"): logout()

    # --- TEACHER DASHBOARD ---
    if role == "teacher":
        st.title("Teacher Dashboard")
        tab1, tab2 = st.tabs(["Grading", "Manage Assignments"])

        # TAB 1: Grading
        with tab1:
            st.subheader("Student Submissions")

            # משיכת נתונים בסיסיים
            all_subs = supabase.table("submissions").select("*").execute().data
            all_users = {u['id']: u['full_name'] for u in
                         supabase.table("users").select("id, full_name").execute().data}
            all_assigns = {a['id']: a for a in supabase.table("assignments").select("*").execute().data}

            if not all_subs:
                st.info("No submissions yet.")

            # Filter Options
            filtered_subs = all_subs
            if all_subs:
                filter_mode = st.radio("Filter By", ["All", "Student", "Assignment"], horizontal=True)
                if filter_mode == "Student":
                    student_ids = sorted(list({s['student_id'] for s in all_subs}), key=lambda x: all_users.get(x, "Unknown"))
                    selected_student = st.selectbox("Select Student", student_ids, format_func=lambda x: all_users.get(x, "Unknown"))
                    filtered_subs = [s for s in all_subs if s['student_id'] == selected_student]
                elif filter_mode == "Assignment":
                    assign_ids = sorted(list({s['assignment_id'] for s in all_subs}), key=lambda x: all_assigns.get(x, {}).get('title', "Unknown"))
                    selected_assign = st.selectbox("Select Assignment", assign_ids, format_func=lambda x: all_assigns.get(x, {}).get('title', "Unknown"))
                    filtered_subs = [s for s in all_subs if s['assignment_id'] == selected_assign]

            for s in filtered_subs:
                # חילוץ שמות לתצוגה
                s_name = all_users.get(s['student_id'], "Unknown Student")
                assignment_data = all_assigns.get(s['assignment_id'], {})
                a_title = assignment_data.get('title', "Unknown Assignment")

                # הכנת המחוון (Rubric) לשליחה ל-AI
                # ודאי שהשדה ב-DB נקרא 'criteria' או 'rubric' - עדכני בהתאם
                rubric_to_send = assignment_data.get("criteria", [])

                with st.expander(f"{s_name} - {a_title}"):
                    st.write(f"Link: {s['link']}")

                    # כפתור הפעלת ה-AI
                    if st.button("🤖 Analyze with AI", key=f"ai_{s['id']}"):
                        with st.spinner("Analyzing project with AI & Dr. Scratch..."):
                            try:
                                # הכנת גוף הבקשה לפי המודל החדש ב-Backend
                                payload = {
                                    "project_url": s['link'],
                                    "rubrics": rubric_to_send
                                }

                                # שליחת הבקשה ל-Backend
                                response = requests.post(f"{API_URL}/teacher/analyze_ai", json=payload)
                                response.raise_for_status()  # זורק שגיאה אם הסטטוס אינו 200
                                res = response.json()

                                # שמירת התוצאות ב-Session State כדי שיופיעו בטופס למטה
                                st.session_state[f"sc_{s['id']}"] = res.get("suggested_score", 0)
                                st.session_state[f"fb_{s['id']}"] = res.get("suggested_feedback", "")

                                st.success("Analysis Complete!")

                                # תצוגת המשוב המפורט למורה (Markdown)
                                st.markdown("### 📝 AI Detailed Feedback")
                                st.markdown(res.get("suggested_feedback", "No detailed feedback provided."))
                                st.divider()

                                # הצגת נתוני Dr. Scratch בנפרד אם קיימים
                                if "raw_dr_scratch" in res:
                                    with st.expander("Technical Data (Dr. Scratch Details)"):
                                        st.json(res["raw_dr_scratch"])

                            except Exception as e:
                                st.error(f"Error during AI analysis: {e}")

                    # טופס מתן ציון סופי
                    with st.form(f"grade_{s['id']}"):
                        st.write("### Final Grading")
                        # הציון והמשוב נמשכים מה-session_state אם ה-AI הופעל, או נשארים ריקים
                        score = st.number_input("Final Score", min_value=0, max_value=100,
                                                value=int(st.session_state.get(f"sc_{s['id']}", 0)))

                        fb = st.text_area("Final Feedback",
                                          value=st.session_state.get(f"fb_{s['id']}", ""),
                                          height=200)

                        if st.form_submit_button("Submit Grade"):
                            try:
                                supabase.table("submissions").update({
                                    "final_score": score,
                                    "feedback": fb,
                                    "status": "Graded"
                                }).eq("id", s['id']).execute()

                                st.success(f"Grade for {s_name} saved successfully!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to save grade: {e}")
        # TAB 2: MANAGE ASSIGNMENTS
        with tab2:
            st.subheader("Manage Assignments")
            mode = st.radio("Mode", ["Create New Assignment", "Edit Existing Assignment"], horizontal=True)

            current_rubric_data = [
                {"name": "קוד ואלגוריתמיקה", "weight": 40,
                 "sub_criteria": [{"name": "Dr Scratch ציון", "weight": 60},
                                  {"name": "כמות אובייקטים", "weight": 10},
                                  {"name": "שימוש באמצעי קלט", "weight": 10},
                                  {"name": "אירועים ומסרים", "weight": 10},
                                  {"name": "למידה עצמית", "weight": 10}]},
                {"name": "שימושיות", "weight": 20,
                 "sub_criteria": [{"name": "עיצוב וחווית המשתמש", "weight": 50},
                                    {"name": "מולטימדיה", "weight": 50}]},
                {"name": "יצירתיות", "weight": 20,
                 "sub_criteria": [{"name": "חדשנות", "weight": 50},
                                  {"name": "פשטות ומהירות", "weight":20},
                                  {"name": "רמה פדגוגית", "weight": 30}]},
                {"name": "הצגה", "weight": 20, "sub_criteria": [{"name": "תיעוד", "weight": 100}]}
            ]

            title_val = ""
            class_val = ""
            target_id = None

            if mode == "Edit Existing Assignment":
                assigns = supabase.table("assignments").select("*").execute().data
                if assigns:
                    opts = {f"{a['title']} ({a['class_name']})": a for a in assigns}
                    sel = st.selectbox("Select Assignment", list(opts.keys()))
                    target_a = opts[sel]

                    title_val = target_a["title"]
                    class_val = target_a["class_name"]
                    target_id = target_a["id"]

                    if isinstance(target_a.get("rubric"), list) and len(target_a["rubric"]) > 0:
                        current_rubric_data = target_a["rubric"]
                else:
                    st.info("No assignments to edit.")

            new_title = st.text_input("Title", value=title_val)
            new_class = st.text_input("Class", value=class_val)

            st.write("### 🏗️ Rubric Structure")
            final_rubric = []
            total_weight = 0
            all_subs_valid = True
            cols = st.columns(4)

            for i in range(4):
                with cols[i]:
                    if i < len(current_rubric_data) and isinstance(current_rubric_data[i], dict):
                        cat_data = current_rubric_data[i]
                    else:
                        cat_data = {"name": f"Category {i + 1}", "weight": 0, "sub_criteria": []}

                    cat_name = cat_data.get("name", f"Category {i + 1}")
                    cat_weight = int(cat_data.get("weight", 0))

                    st.markdown(f"#### {cat_name}")
                    w = st.number_input(f"Weight %", 0, 100, cat_weight, key=f"w_{i}")
                    total_weight += w

                    subs = cat_data.get("sub_criteria", [])
                    if not isinstance(subs, list): subs = []
                    df = pd.DataFrame(subs)
                    if "name" not in df.columns or "weight" not in df.columns:
                        df = pd.DataFrame(columns=["name", "weight"])

                    st.caption("Sub-Criteria")
                    edited_df = st.data_editor(
                        df, num_rows="dynamic", key=f"ed_{i}", hide_index=True,
                        column_config={
                            "name": st.column_config.TextColumn("Criteria Name", required=True),
                            "weight": st.column_config.NumberColumn("Weight", min_value=0, max_value=100, required=True)
                        }
                    )

                    if "weight" in edited_df.columns:
                        sub_sum = edited_df["weight"].sum()
                    else:
                        sub_sum = 0

                    if sub_sum != 100:
                        st.error(f"Sum: {sub_sum}%")
                        all_subs_valid = False
                    else:
                        st.success("100% ✅")

                    final_rubric.append({
                        "name": cat_name,
                        "weight": w,
                        "sub_criteria": edited_df.to_dict(orient="records")
                    })

            st.divider()

            if total_weight != 100:
                st.error(f"Total Category Weight: {total_weight}% (Must be 100%)")
                main_valid = False
            else:
                st.success(f"Total Category Weight: {total_weight}% ✅")
                main_valid = True

            btn_text = "Create Assignment" if mode == "Create New Assignment" else "Update Assignment"
            c_btn1, c_btn2 = st.columns([1, 4])
            with c_btn1:
                if st.button(btn_text):
                    if not main_valid or not all_subs_valid or not new_class.strip():
                        st.error("Please fix errors above.")
                    else:
                        rubric_payload = {
                            "teacher_id": user['id'],
                            "title": new_title,
                            "class_name": new_class.strip(),
                            "criteria": final_rubric
                        }
                        try:
                            if mode == "Create New Assignment":
                                res = requests.post(f"{API_URL}/teacher/rubrics", json=rubric_payload)
                            else:
                                res = requests.put(f"{API_URL}/teacher/rubrics/{target_id}", json=rubric_payload)
                            res.raise_for_status()
                            st.success("Success!")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save: {e}")

            if mode == "Edit Existing Assignment" and target_id:
                with c_btn2:
                    if st.button("🗑️ Delete Assignment", type="primary"):
                        try:
                            res = requests.delete(f"{API_URL}/teacher/rubrics/{target_id}")
                            res.raise_for_status()
                            st.success("Deleted!")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

    # --- STUDENT DASHBOARD ---
    elif role == "student":
        st.title("My Dashboard")
        student_class = user.get('class_name', '').strip()

        if not student_class:
            st.warning("⚠️ You do not have a Class Name assigned. You won't see any assignments.")

        assigns = supabase.table("assignments").select("*").eq("class_name", student_class).execute().data
        subs = supabase.table("submissions").select("*").eq("student_id", user['id']).execute().data
        sub_map = {s['assignment_id']: s for s in subs}

        if not assigns and student_class:
            st.info(f"No assignments found for class: '{student_class}'")

        for a in assigns:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(a['title'])
                s = sub_map.get(a['id'])
                if s:
                    c1.write(f"Status: {s['status']}")
                    if s['status'] == "Graded":
                        c2.metric("Score", s['final_score'])
                        c1.success(s['feedback'])
                    else:
                        with c2.popover("Edit Link"):
                            l_edit = st.text_input("New Link", value=s['link'], key=f"edit_{a['id']}")
                            if st.button("Update", key=f"update_{a['id']}"):
                                if not l_edit:
                                    st.error("Please enter a link.")
                                elif not l_edit.startswith("https://scratch.mit.edu/projects/"):
                                    st.error("Link must start with https://scratch.mit.edu/projects/")
                                else:
                                    try:
                                        project_id = l_edit.rstrip("/").split("/")[-1]
                                        check_resp = requests.get(f"https://api.scratch.mit.edu/projects/{project_id}", timeout=5)
                                        if check_resp.status_code == 200:
                                            supabase.table("submissions").update({"link": l_edit}).eq("id", s['id']).execute()
                                            st.success("Updated!")
                                            st.rerun()
                                        else:
                                            st.error("Project does not exist or is unshared (API Check Failed).")
                                    except Exception as e:
                                        st.error(f"Error checking link: {e}")
                else:
                    c1.info("Not Submitted")
                    with c2.popover("Submit"):
                        l = st.text_input("Link", key=a['id'])
                        if st.button("Send", key=f"b_{a['id']}"):
                            if not l:
                                st.error("Please enter a link.")
                            elif not l.startswith("https://scratch.mit.edu/projects/"):
                                st.error("Link must start with https://scratch.mit.edu/projects/")
                            else:
                                try:
                                    project_id = l.rstrip("/").split("/")[-1]
                                    check_resp = requests.get(f"https://api.scratch.mit.edu/projects/{project_id}", timeout=5)
                                    if check_resp.status_code == 200:
                                        requests.post(f"{API_URL}/student/submit",
                                                      json={"student_id": user['id'], "assignment_id": a['id'], "link": l})
                                        st.success("Sent!")
                                        st.rerun()
                                    else:
                                        st.error("Project does not exist or is unshared (API Check Failed).")
                                except Exception as e:
                                    st.error(f"Error checking link: {e}")

    # --- ADMIN VIEW ---
    elif role == "admin":
        st.title("Admin Overview")

        # 1. Fetch Data
        users_data = supabase.table("users").select("*").execute().data
        assignments_data = supabase.table("assignments").select("*").execute().data
        submissions_data = supabase.table("submissions").select("*").execute().data

        # 2. Key Metrics
        graded_count = len([s for s in submissions_data if s['status'] == 'Graded'])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Students", len([u for u in users_data if u['role'] == 'student']))
        m2.metric("Teachers", len([u for u in users_data if u['role'] == 'teacher']))
        m3.metric("Assignments", len(assignments_data) if assignments_data else 0)
        m4.metric("Submissions", len(submissions_data), f"{graded_count} Graded")

        st.divider()

        # 3. ADVANCED STATISTICS (NEW)
        c_chart1, c_chart2 = st.columns(2)

        # Chart 1: Average Grade by Class
        with c_chart1:
            st.subheader("📊 Class Performance")
            if assignments_data and submissions_data:
                # Map Assignment ID -> Class Name
                assign_class_map = {a['id']: a['class_name'] for a in assignments_data}

                # Build Data: Class Name -> List of Grades
                class_grades = {}
                for s in submissions_data:
                    aid = s['assignment_id']
                    if aid in assign_class_map and s.get('final_score') is not None:
                        cname = assign_class_map[aid]
                        if cname not in class_grades: class_grades[cname] = []
                        class_grades[cname].append(s['final_score'])

                # Calculate Averages
                avg_data = {"Class": [], "Average Score": []}
                for cname, grades in class_grades.items():
                    avg_data["Class"].append(cname)
                    avg_data["Average Score"].append(sum(grades) / len(grades))

                if avg_data["Class"]:
                    st.bar_chart(pd.DataFrame(avg_data).set_index("Class"))
                else:
                    st.info("No graded submissions yet.")
            else:
                st.info("Insufficient data.")

        # Chart 2: Status Distribution
        with c_chart2:
            st.subheader("🍩 Submission Status")
            if submissions_data:
                status_counts = pd.Series([s['status'] for s in submissions_data]).value_counts()
                st.bar_chart(status_counts)  # Pie chart requires plotly/altair, bar is safer for basic .streamlit
            else:
                st.info("No submissions.")

        st.divider()

        # 4. Detailed Table
        st.subheader("📋 Detailed Assignment Stats")
        if assignments_data:
            stats_data = []
            for a in assignments_data:
                these_subs = [s for s in submissions_data if s['assignment_id'] == a['id']]
                graded_subs = [s['final_score'] for s in these_subs if s.get('final_score') is not None]
                avg_grade = sum(graded_subs) / len(graded_subs) if graded_subs else 0

                stats_data.append({
                    "Class": a['class_name'],
                    "Assignment": a['title'],
                    "Submissions": len(these_subs),
                    "Avg Grade": f"{avg_grade:.1f}"
                })
            st.dataframe(pd.DataFrame(stats_data), width='stretch', hide_index=True)

        # 5. Top Students Leaderboard (NEW)
        with st.expander("🏆 Top Performing Students"):
            if users_data and submissions_data:
                # Student ID -> Name
                student_map = {u['id']: u.get('full_name', u['username']) for u in users_data if u['role'] == 'student'}
                # Student ID -> Grades List
                student_grades = {}
                for s in submissions_data:
                    sid = s['student_id']
                    if sid in student_map and s.get('final_score') is not None:
                        if sid not in student_grades: student_grades[sid] = []
                        student_grades[sid].append(s['final_score'])

                leaderboard = []
                for sid, grades in student_grades.items():
                    leaderboard.append({
                        "Student": student_map[sid],
                        "Average Score": sum(grades) / len(grades),
                        "Projects Completed": len(grades)
                    })

                if leaderboard:
                    df_leader = pd.DataFrame(leaderboard).sort_values("Average Score", ascending=False)
                    st.dataframe(df_leader,  width='stretch', hide_index=True)
                else:
                    st.info("No graded students yet.")

        st.divider()

        # 6. User Management
        st.subheader("Create New User")
        with st.form("create_user_form"):
            c1, c2 = st.columns(2)
            new_username = c1.text_input("Username")
            new_password = c2.text_input("Password", type="password")
            new_fullname = c1.text_input("Full Name")
            new_role = c2.selectbox("Role", ["student", "teacher", "admin"])
            new_class = st.text_input("Class Name") if new_role == "student" else ""

            if st.form_submit_button("Create User"):
                if new_username and new_password:
                    try:
                        user_payload = {
                            "username": new_username, "password": new_password,
                            "full_name": new_fullname, "role": new_role,
                            "class_name": new_class.strip() if new_role == "student" else None
                        }
                        supabase.table("users").insert(user_payload).execute()
                        st.success(f"User '{new_username}' created!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # User Database Table
        if users_data:
            df = pd.DataFrame(users_data)
            cols = ["username", "role", "full_name", "class_name", "password"]
            st.dataframe(df[[c for c in cols if c in df.columns]], width='stretch', hide_index=True)