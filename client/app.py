import streamlit as st
import time
import uuid
import random

st.set_page_config(page_title="CodeImpact AI", page_icon="🎓", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .block-container { max-width: 1200px; padding-top: 2rem; }
    .role-card {
        background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;
        text-align: center; height: 180px; display: flex; flex-direction: column;
        justify-content: center; align-items: center; cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s;
    }
    .role-card:hover { border-color: #FF4B4B; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .login-box { background: white; padding: 40px; border-radius: 12px; border: 1px solid #eee; }

    /* RUBRIC STYLES */
    .rubric-box { border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; background-color: #f9f9f9; margin-bottom: 10px; }
    .total-weight-ok { color: green; font-weight: bold; }
    .total-weight-bad { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 1. MOCK DATABASE ---
if "users" not in st.session_state:
    st.session_state.users = [
        {"id": 1, "username": "student", "password": "123", "role": "student", "name": "Alex Student",
         "class": "Class A"},
        {"id": 2, "username": "teacher", "password": "123", "role": "teacher", "name": "Mr. Smith",
         "classes": ["Class A", "Class B"]},
        {"id": 3, "username": "admin", "password": "123", "role": "admin", "name": "Principal Skinner"}
    ]

# "Assignments" are the Projects the TEACHER creates (e.g. "Pacman")
if "assignments" not in st.session_state:
    st.session_state.assignments = [
        {
            "id": "a1", "teacher_id": 2, "class_name": "Class A", "title": "Pacman Game",
            "rubric": [
                {"category": "Code Efficiency", "weight": 50, "sub_criteria": ["Uses Loops", "No Duplicate Code"]},
                {"category": "Creativity", "weight": 50, "sub_criteria": ["Original Sprites", "Sound Effects"]}
            ]
        }
    ]

# "Submissions" are what STUDENTS upload
if "submissions" not in st.session_state:
    st.session_state.submissions = [
        {"id": "s1", "assignment_id": "a1", "student_id": 1, "link": "https://scratch.mit.edu/projects/101",
         "status": "Pending", "scores": {}, "final_score": 0, "feedback": ""}
    ]

# --- 2. NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "auth_user" not in st.session_state: st.session_state.auth_user = None


def navigate(page): st.session_state.page = page; st.rerun()


def logout(): st.session_state.auth_user = None; navigate("home")


# ==========================================
# SCREEN 1: HOME
# ==========================================
if st.session_state.page == "home":
    st.title("CodeImpact AI 🚀")
    st.write("### Where Code Meets Social Impact")
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="role-card"><h2>👨‍🎓</h2><h3>Student</h3></div>', unsafe_allow_html=True)
        if st.button("Student Access"): st.session_state.role = "student"; navigate("login")
    with c2:
        st.markdown('<div class="role-card"><h2>👩‍🏫</h2><h3>Teacher</h3></div>', unsafe_allow_html=True)
        if st.button("Teacher Access"): st.session_state.role = "teacher"; navigate("login")
    with c3:
        st.markdown('<div class="role-card"><h2>🛡️</h2><h3>Admin</h3></div>', unsafe_allow_html=True)
        if st.button("Admin Access"): st.session_state.role = "admin"; navigate("login")

# ==========================================
# SCREEN 2: LOGIN
# ==========================================
elif st.session_state.page == "login":
    role = st.session_state.role
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.info(f"🔑 **Credentials:** Name: `{role}` | Pass: `123`")
        with st.form("login"):
            st.markdown(f"### {role.capitalize()} Login")
            u = st.text_input("Name");
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                user = next(
                    (x for x in st.session_state.users if x["username"].lower() == u.lower() and x["password"] == p),
                    None)
                if user and user['role'] == role:
                    st.session_state.auth_user = user
                    navigate("dashboard")
                else:
                    st.error("Invalid Credentials or Wrong Role")
        if st.button("Back"): navigate("home")

# ==========================================
# SCREEN 3: TEACHER DASHBOARD (THE FOCUS)
# ==========================================
elif st.session_state.page == "dashboard" and st.session_state.auth_user['role'] == "teacher":
    user = st.session_state.auth_user
    st.sidebar.title(f"👤 {user['name']}")
    menu = st.sidebar.radio("Menu", ["Create Project & Rubric", "Classroom Grading"])
    if st.sidebar.button("Logout"): logout()

    # --- TAB A: DEFINE PROJECT (RUBRICS) ---
    if menu == "Create Project & Rubric":
        st.title("Define New Class Project")
        st.info("Define the project requirements and the strict grading rubric below.")

        with st.container(border=True):
            # 1. Basic Info
            c_name = st.selectbox("Assign to Class", user['classes'])
            p_title = st.text_input("Project Name (e.g., 'Maze Game')")

            st.divider()
            st.subheader("📊 Personalized Rubric")

            # 2. Dynamic Rubric Builder
            if "temp_rubric" not in st.session_state:
                st.session_state.temp_rubric = [{"category": "", "weight": 0, "sub_criteria": []}]

            # Display Inputs for Categories
            total_weight = 0
            updated_rubric = []

            for i, item in enumerate(st.session_state.temp_rubric):
                with st.container():
                    st.markdown(f"**Main Category {i + 1}**")
                    c1, c2 = st.columns([3, 1])
                    cat_name = c1.text_input(f"Category Name", item['category'], key=f"cat_{i}")
                    cat_weight = c2.number_input(f"Weight %", 0, 100, item['weight'], key=f"w_{i}")

                    # Sub-Categories (Checkboxes)
                    sub_text = st.text_area(f"Secondary Categories (Comma separated)", ", ".join(item['sub_criteria']),
                                            key=f"sub_{i}", height=68,
                                            placeholder="e.g., Uses Loops, Correct Variables")
                    sub_list = [s.strip() for s in sub_text.split(",") if s.strip()]

                    updated_rubric.append({"category": cat_name, "weight": cat_weight, "sub_criteria": sub_list})
                    total_weight += cat_weight
                    st.divider()

            # Buttons to Add/Remove Categories
            b1, b2 = st.columns(2)
            if b1.button("➕ Add Main Category"):
                st.session_state.temp_rubric.append({"category": "", "weight": 0, "sub_criteria": []})
                st.rerun()
            if len(st.session_state.temp_rubric) > 1 and b2.button("➖ Remove Last"):
                st.session_state.temp_rubric.pop()
                st.rerun()

            # 3. Validation (100% Rule)
            st.write("")
            if total_weight == 100:
                st.markdown(f"<p class='total-weight-ok'>Total Weight: {total_weight}% (Perfect)</p>",
                            unsafe_allow_html=True)

                if st.button("💾 Publish Project to Students"):
                    if p_title:
                        new_assign = {
                            "id": str(uuid.uuid4())[:4],
                            "teacher_id": user['id'],
                            "class_name": c_name,
                            "title": p_title,
                            "rubric": updated_rubric
                        }
                        st.session_state.assignments.append(new_assign)
                        st.success("Project Published! Students can now submit.")
                        st.session_state.temp_rubric = [{"category": "", "weight": 0, "sub_criteria": []}]  # Reset
                    else:
                        st.error("Please enter a Project Name.")
            else:
                st.markdown(f"<p class='total-weight-bad'>Total Weight: {total_weight}% (Must be exactly 100%)</p>",
                            unsafe_allow_html=True)
                st.button("Publish Project", disabled=True, help="Fix weights to 100% first")

    # --- TAB B: GRADING ---
    elif menu == "Classroom Grading":
        st.title("Grading Dashboard")

        # 1. Filter
        sel_class = st.selectbox("Select Class", user['classes'])

        # 2. Get Submissions for this class
        # (Logic: Find assignments for this class -> Find submissions for those assignments)
        class_assign_ids = [a['id'] for a in st.session_state.assignments if a['class_name'] == sel_class]
        class_subs = [s for s in st.session_state.submissions if s['assignment_id'] in class_assign_ids]

        if not class_subs:
            st.info("No submissions found for this class.")

        for sub in class_subs:
            # Get Student Name & Project Details
            s_name = next((u['name'] for u in st.session_state.users if u['id'] == sub['student_id']), "Unknown")
            assign = next((a for a in st.session_state.assignments if a['id'] == sub['assignment_id']), None)

            with st.expander(f"{s_name} - {assign['title']} ({sub['status']})"):
                st.write(f"🔗 **Link:** {sub['link']}")

                if sub['status'] == "Pending":
                    st.write("### Assessment")

                    # AI BUTTON
                    if st.button("✨ Auto-Grade with AI", key=f"ai_{sub['id']}"):
                        with st.spinner("Analyzing Scratch Blocks..."):
                            time.sleep(1.5)  # Fake AI delay
                            st.session_state[f"ai_res_{sub['id']}"] = {
                                "scores": {r['category']: random.randint(70, 100) for r in assign['rubric']},
                                "feedback": "Good logic structure. Loops are used efficiently."
                            }

                    # GRADING FORM
                    with st.form(f"grade_{sub['id']}"):
                        ai_data = st.session_state.get(f"ai_res_{sub['id']}", {})
                        final_cats = {}

                        for r in assign['rubric']:
                            st.markdown(f"**{r['category']} ({r['weight']}%)**")
                            # Secondary Categories (Checkboxes)
                            for sub_c in r['sub_criteria']:
                                st.checkbox(sub_c, key=f"{sub['id']}_{sub_c}")

                            # Score Input
                            def_score = ai_data.get('scores', {}).get(r['category'], 0)
                            score = st.number_input(f"Score for {r['category']}", 0, 100, def_score,
                                                    key=f"s_{sub['id']}_{r['category']}")
                            final_cats[r['category']] = score
                            st.divider()

                        fb = st.text_area("Feedback", ai_data.get('feedback', ""))

                        if st.form_submit_button("Submit Final Grade"):
                            # Calculate Weighted Score
                            total = sum([final_cats[c['category']] * (c['weight'] / 100) for c in assign['rubric']])
                            sub['final_score'] = int(total)
                            sub['feedback'] = fb
                            sub['status'] = "Graded"
                            st.success("Graded Successfully!")
                            st.rerun()
                else:
                    st.success(f"Final Score: {sub['final_score']}")
                    st.info(sub['feedback'])

# ==========================================
# SCREEN 4: STUDENT DASHBOARD
# ==========================================
elif st.session_state.page == "dashboard" and st.session_state.auth_user['role'] == "student":
    user = st.session_state.auth_user
    st.sidebar.title(f"👤 {user['name']}")
    if st.sidebar.button("Logout"): logout()

    st.title("My Assignments")

    # Find Assignments for my Class
    my_assigns = [a for a in st.session_state.assignments if a['class_name'] == user['class']]

    for assign in my_assigns:
        # Check if I already submitted
        existing_sub = next((s for s in st.session_state.submissions if
                             s['assignment_id'] == assign['id'] and s['student_id'] == user['id']), None)

        with st.container(border=True):
            st.subheader(assign['title'])

            # Show Rubric
            with st.expander("View Grading Rubric"):
                for r in assign['rubric']:
                    st.write(f"- **{r['category']} ({r['weight']}%)**: {', '.join(r['sub_criteria'])}")

            if existing_sub:
                if existing_sub['status'] == "Graded":
                    st.success(f"**Grade:** {existing_sub['final_score']}/100")
                    st.info(f"**Feedback:** {existing_sub['feedback']}")
                else:
                    st.warning("Status: Pending Teacher Review")
            else:
                # Submission Form
                l = st.text_input("Scratch Link", key=f"link_{assign['id']}")
                if st.button("Submit Project", key=f"btn_{assign['id']}"):
                    if l:
                        new_sub = {
                            "id": str(uuid.uuid4())[:4],
                            "assignment_id": assign['id'],
                            "student_id": user['id'],
                            "link": l,
                            "status": "Pending",
                            "final_score": 0,
                            "feedback": ""
                        }
                        st.session_state.submissions.append(new_sub)
                        st.success("Submitted!")
                        st.rerun()
                    else:
                        st.error("Please enter a link.")

# ==========================================
# SCREEN 5: ADMIN DASHBOARD
# ==========================================
elif st.session_state.page == "dashboard" and st.session_state.auth_user['role'] == "admin":
    st.sidebar.button("Logout", on_click=logout)
    st.title("System Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Users", len(st.session_state.users))
    c2.metric("Assignments Created", len(st.session_state.assignments))
    c3.metric("Submissions", len(st.session_state.submissions))

    st.write("### Database")
    st.json(st.session_state.users)