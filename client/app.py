import time
import streamlit as st
import pandas as pd
import requests
from supabase import create_client
from pathlib import Path

from api.client import API_URL

# ============================================================
# CONFIGURATION
# מומלץ לשים מפתחות ב-.streamlit/secrets.toml ולא בקוד
# ============================================================
SUPABASE_URL = "https://hmouoztlgrsotauzohgm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhtb3VvenRsZ3Jzb3RhdXpvaGdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzMjgwNjUsImV4cCI6MjA3OTkwNDA2NX0.7lICVEIkYaG_629xN_nVPUJspUgkhRswkKJKTF2TNBg"

# ============================================================
# UI TEXT (עברית בלבד) + מיפויים לערכי DB באנגלית
# ============================================================
ROLE_HE = {"student": "תלמיד/ה", "teacher": "מורה", "admin": "מנהל/ת"}

STATUS_HE = {
    "Graded": "נבדק",
    "Submitted": "הוגש",
    "Pending": "ממתין",
}

FILTER_MODE_HE = {
    "All": "הכל",
    "Student": "תלמיד/ה",
    "Assignment": "מטלה",
}

MODE_HE = {
    "Create New Assignment": "יצירת מטלה חדשה",
    "Edit Existing Assignment": "עריכת מטלה קיימת",
}

def he_role(role: str) -> str:
    return ROLE_HE.get(role, role)

def he_status(status: str) -> str:
    return STATUS_HE.get(status, status)

# ============================================================
# HELPERS
# ============================================================
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ לא נמצא קובץ CSS: {css_path}")

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"❌ נכשל החיבור למסד הנתונים: {e}")
        return None

def navigate(page: str):
    st.session_state.page = page
    st.rerun()

def logout():
    st.session_state.auth_user = None
    navigate("home")

# ============================================================
# APP INIT
# ============================================================
supabase = init_supabase()
st.set_page_config(page_title="CodeImpact AI", page_icon="🎓", layout="wide")
load_css()

if "page" not in st.session_state:
    st.session_state.page = "home"
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "target" not in st.session_state:
    st.session_state.target = None

# ============================================================
# PAGE: HOME
# ============================================================
if st.session_state.page == "home":
    st.markdown("<h1 style='text-align: center;'>CodeImpact AI 🚀</h1>", unsafe_allow_html=True)
    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""<div class="role-card"><h1>👨‍🎓</h1><h3>תלמיד/ה</h3></div>""", unsafe_allow_html=True)
        if st.button("התחברות תלמיד/ה", width='stretch'):
            st.session_state.target = "student"
            navigate("login")

    with c2:
        st.markdown("""<div class="role-card"><h1>🏫</h1><h3>מורה</h3></div>""", unsafe_allow_html=True)
        if st.button("התחברות מורה", width='stretch'):
            st.session_state.target = "teacher"
            navigate("login")

    with c3:
        st.markdown("""<div class="role-card"><h1>🛡️</h1><h3>מנהל/ת</h3></div>""", unsafe_allow_html=True)
        if st.button("התחברות מנהל/ת", width='stretch'):
            st.session_state.target = "admin"
            navigate("login")

# ============================================================
# PAGE: LOGIN
# ============================================================
elif st.session_state.page == "login":
    tgt = st.session_state.target

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login"):
            st.markdown(
                f"<h3 style='text-align: center;'>התחברות {he_role(tgt)}</h3>",
                unsafe_allow_html=True
            )

            u = st.text_input("שם משתמש").strip()
            p = st.text_input("סיסמה", type="password").strip()

            # בקוד האנגלי היה תלמיד עם הזנת כיתה בלוגין
            c_name = ""
            if tgt == "student":
                c_name = st.text_input("שם כיתה").strip()
                st.caption("טיפ: אם אין לך משתמש, החשבון ייווצר אוטומטית אם הכיתה קיימת.")

            submitted = st.form_submit_button("כניסה", width='stretch')

            if submitted:
                if supabase is None:
                    st.error("❌ אין חיבור ל-Supabase.")
                elif not u or not p:
                    st.error("אנא הזן/י שם משתמש וסיסמה.")
                else:
                    # חיפוש משתמש קיים לפי username (יותר יעיל מאשר select all)
                    res = supabase.table("users").select("*").eq("username", u).execute()
                    found_user = res.data[0] if res.data else None

                    if found_user:
                        # משתמש קיים
                        if tgt == "student":
                            # בדיקת התאמת כיתה
                            if found_user.get("class_name") != c_name:
                                st.error(
                                    f"⛔ אין הרשאה: אתה רשום/ה לכיתה '{found_user.get('class_name')}', לא '{c_name}'."
                                )
                            elif str(found_user.get("password", "")) == p:
                                st.session_state.auth_user = found_user
                                navigate("dashboard")
                            else:
                                st.error("סיסמה שגויה.")
                        else:
                            # מורה/מנהל - לוגין רגיל
                            if str(found_user.get("password", "")) == p:
                                st.session_state.auth_user = found_user
                                navigate("dashboard")
                            else:
                                st.error("סיסמה שגויה.")

                    elif tgt == "student":
                        # רישום אוטומטי לתלמיד חדש (מהקוד האנגלי)
                        if not c_name:
                            st.error("שם כיתה הוא חובה לתלמיד חדש.")
                        else:
                            class_check = supabase.table("assignments").select("class_name").eq("class_name", c_name).execute()
                            if not class_check.data:
                                st.error(f"הכיתה '{c_name}' לא קיימת. פנה/י למורה.")
                            else:
                                try:
                                    new_student = {
                                        "username": u,
                                        "password": p,
                                        "role": "student",
                                        "full_name": u,
                                        "class_name": c_name
                                    }
                                    insert_res = supabase.table("users").insert(new_student).execute()
                                    if insert_res.data:
                                        st.success(f"ברוך/ה הבא/ה! נוצר חשבון עבור {u} בכיתה {c_name}.")
                                        st.session_state.auth_user = insert_res.data[0]
                                        time.sleep(1)
                                        navigate("dashboard")
                                    else:
                                        st.error("נכשלה יצירת משתמש (לא הוחזרו נתונים).")
                                except Exception as e:
                                    st.error(f"❌ שגיאה ביצירת חשבון: {e}")
                    else:
                        st.error("משתמש לא נמצא.")

    if st.button("חזרה"):
        navigate("home")

# ============================================================
# PAGE: DASHBOARD
# ============================================================
elif st.session_state.page == "dashboard":
    user = st.session_state.auth_user
    if not user:
        navigate("home")

    role = user["role"]

    st.sidebar.title(f"👤 {user.get('full_name', user['username'])}")
    if st.sidebar.button("התנתקות"):
        logout()

    # ========================================================
    # TEACHER DASHBOARD
    # ========================================================
    if role == "teacher":
        st.title("לוח מורה")
        tab1, tab2 = st.tabs(["בדיקת עבודות", "ניהול מטלות"])

        # ----------------------------
        # TAB 1: GRADING
        # ----------------------------
        with tab1:
            st.subheader("הגשות תלמידים")

            all_subs = supabase.table("submissions").select("*").execute().data
            all_users = {u["id"]: u.get("full_name", u.get("username", "לא ידוע/ה"))
                         for u in supabase.table("users").select("id, full_name, username").execute().data}
            all_assigns = {a["id"]: a for a in supabase.table("assignments").select("*").execute().data}

            if not all_subs:
                st.info("אין עדיין הגשות.")

            filtered_subs = all_subs

            if all_subs:
                filter_mode_en = st.radio(
                    "סינון לפי",
                    ["All", "Student", "Assignment"],
                    horizontal=True,
                    format_func=lambda x: FILTER_MODE_HE.get(x, x)
                )

                if filter_mode_en == "Student":
                    student_ids = sorted(
                        list({s["student_id"] for s in all_subs}),
                        key=lambda x: all_users.get(x, "לא ידוע/ה")
                    )
                    selected_student = st.selectbox(
                        "בחר/י תלמיד/ה",
                        student_ids,
                        format_func=lambda x: all_users.get(x, "לא ידוע/ה")
                    )
                    filtered_subs = [s for s in all_subs if s["student_id"] == selected_student]

                elif filter_mode_en == "Assignment":
                    assign_ids = sorted(
                        list({s["assignment_id"] for s in all_subs}),
                        key=lambda x: all_assigns.get(x, {}).get("title", "מטלה לא ידועה")
                    )
                    selected_assign = st.selectbox(
                        "בחר/י מטלה",
                        assign_ids,
                        format_func=lambda x: all_assigns.get(x, {}).get("title", "מטלה לא ידועה")
                    )
                    filtered_subs = [s for s in all_subs if s["assignment_id"] == selected_assign]

            for s in filtered_subs:
                s_name = all_users.get(s["student_id"], "תלמיד/ה לא ידוע/ה")
                assignment_data = all_assigns.get(s["assignment_id"], {})
                a_title = assignment_data.get("title", "מטלה לא ידועה")

                # חשוב: לא לשנות keys שהשרת מצפה להם.
                rubric_to_send = assignment_data.get("criteria", [])

                with st.expander(f"{s_name} - {a_title}"):
                    st.write(f"קישור: {s['link']}")

                    if st.button("🤖 ניתוח עם AI", key=f"ai_{s['id']}"):
                        with st.spinner("מנתח פרויקט עם AI ו-Dr. Scratch..."):
                            try:
                                payload = {
                                    "project_url": s["link"],
                                    "rubrics": rubric_to_send
                                }
                                response = requests.post(f"{API_URL}/teacher/analyze_ai", json=payload, timeout=120)
                                response.raise_for_status()
                                res = response.json()

                                st.session_state[f"sc_{s['id']}"] = res.get("suggested_score", 0)
                                st.session_state[f"fb_{s['id']}"] = res.get("suggested_feedback", "")

                                st.success("הניתוח הושלם ✅")

                                st.markdown("### 📝 משוב מפורט מה-AI")
                                st.markdown(res.get("suggested_feedback", "לא התקבל משוב מפורט."))
                                st.divider()

                                if "raw_dr_scratch" in res:
                                    with st.expander("נתונים טכניים (פרטי Dr. Scratch)"):
                                        st.json(res["raw_dr_scratch"])

                            except Exception as e:
                                st.error(f"❌ שגיאה במהלך ניתוח AI: {e}")

                    with st.form(f"grade_{s['id']}"):
                        st.write("### ציון סופי")

                        score = st.number_input(
                            "ציון סופי (0–100)",
                            min_value=0,
                            max_value=100,
                            value=int(st.session_state.get(f"sc_{s['id']}", 0))
                        )

                        fb = st.text_area(
                            "משוב סופי",
                            value=st.session_state.get(f"fb_{s['id']}", ""),
                            height=200
                        )

                        if st.form_submit_button("שמירת ציון"):
                            try:
                                supabase.table("submissions").update({
                                    "final_score": score,
                                    "feedback": fb,
                                    "status": "Graded"  # חשוב: להשאיר באנגלית ב-DB
                                }).eq("id", s["id"]).execute()

                                st.success(f"הציון עבור {s_name} נשמר ✅")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ שמירה נכשלה: {e}")

        # ----------------------------
        # TAB 2: MANAGE ASSIGNMENTS
        # ----------------------------
        with tab2:
            st.subheader("ניהול מטלות")

            mode_en = st.radio(
                "מצב",
                ["Create New Assignment", "Edit Existing Assignment"],
                horizontal=True,
                format_func=lambda x: MODE_HE.get(x, x)
            )

            # תבנית ברירת מחדל למחוון
            current_rubric_data = [
                {"name": "קוד ואלגוריתמיקה", "weight": 40,
                 "sub_criteria": [{"name": "ציון DR Scratch", "weight": 60},
                                  {"name": "כמות אובייקטים", "weight": 10},
                                  {"name": "שימוש באמצעי קלט", "weight": 10},
                                  {"name": "אירועים ומסרים", "weight": 10},
                                  {"name": "למידה עצמית", "weight": 10}]},
                {"name": "שימושיות", "weight": 20,
                 "sub_criteria": [{"name": "עיצוב וחווית המשתמש", "weight": 50},
                                  {"name": "מולטימדיה", "weight": 50}]},
                {"name": "יצירתיות", "weight": 20,
                 "sub_criteria": [{"name": "חדשנות", "weight": 50},
                                  {"name": "פשטות ובהירות", "weight": 20},
                                  {"name": "רמה פדגוגית", "weight": 30}]},
                {"name": "הצגה", "weight": 20, "sub_criteria": [{"name": "תיעוד", "weight": 100}]}
            ]

            title_val = ""
            class_val = ""
            target_id = None

            if mode_en == "Edit Existing Assignment":
                assigns = supabase.table("assignments").select("*").execute().data
                if assigns:
                    opts = {f"{a['title']} ({a['class_name']})": a for a in assigns}
                    sel = st.selectbox("בחר/י מטלה", list(opts.keys()))
                    target_a = opts[sel]

                    title_val = target_a["title"]
                    class_val = target_a["class_name"]
                    target_id = target_a["id"]

                    # אם אצלך ב-DB נשמר תחת rubric (כמו בקוד המקורי שלך), נשאיר התאמה:
                    if isinstance(target_a.get("rubric"), list) and len(target_a["rubric"]) > 0:
                        current_rubric_data = target_a["rubric"]
                else:
                    st.info("אין מטלות לעריכה.")

            new_title = st.text_input("כותרת", value=title_val)
            new_class = st.text_input("כיתה", value=class_val)

            st.write("### 🏗️ מבנה מחוון")
            final_rubric = []
            total_weight = 0
            all_subs_valid = True
            cols = st.columns(4)

            for i in range(4):
                with cols[i]:
                    if i < len(current_rubric_data) and isinstance(current_rubric_data[i], dict):
                        cat_data = current_rubric_data[i]
                    else:
                        cat_data = {"name": f"קטגוריה {i + 1}", "weight": 0, "sub_criteria": []}

                    cat_name = cat_data.get("name", f"קטגוריה {i + 1}")
                    cat_weight = int(cat_data.get("weight", 0))

                    st.markdown(f"#### {cat_name}")
                    w = st.number_input("משקל (%)", 0, 100, cat_weight, key=f"w_{i}")
                    total_weight += w

                    subs = cat_data.get("sub_criteria", [])
                    if not isinstance(subs, list):
                        subs = []

                    df = pd.DataFrame(subs)
                    if "name" not in df.columns or "weight" not in df.columns:
                        df = pd.DataFrame(columns=["name", "weight"])

                    st.caption("תתי־קריטריונים")

                    # ✅ נועל את עמודת name + לא מאפשר הוספה/מחיקה של שורות
                    edited_df = st.data_editor(
                        df,
                        key=f"ed_{i}",
                        hide_index=True,
                        width="stretch",
                        num_rows="fixed",
                        disabled=["name"],
                        column_config={
                            "name": st.column_config.TextColumn("שם קריטריון", required=True),
                            "weight": st.column_config.NumberColumn("משקל", min_value=0, max_value=100, required=True)
                        }
                    )

                    sub_sum = edited_df["weight"].sum() if "weight" in edited_df.columns else 0

                    if sub_sum != 100:
                        st.error(f"סכום תתי־קריטריונים: {sub_sum}%")
                        all_subs_valid = False
                    else:
                        st.success("סכום תתי־קריטריונים: 100% ✅")

                    final_rubric.append({
                        "name": cat_name,
                        "weight": w,
                        "sub_criteria": edited_df.to_dict(orient="records")
                    })

            st.divider()

            if total_weight != 100:
                st.error(f"סה״כ משקל קטגוריות: {total_weight}% (חייב להיות 100%)")
                main_valid = False
            else:
                st.success(f"סה״כ משקל קטגוריות: {total_weight}% ✅")
                main_valid = True

            btn_text = "יצירת מטלה" if mode_en == "Create New Assignment" else "עדכון מטלה"
            c_btn1, c_btn2 = st.columns([1, 4])

            with c_btn1:
                if st.button(btn_text):
                    if not main_valid or not all_subs_valid or not new_class.strip():
                        st.error("אנא תקן/י את השגיאות למעלה וודא/י ששדה כיתה אינו ריק.")
                    else:
                        rubric_payload = {
                            "teacher_id": user["id"],
                            "title": new_title,
                            "class_name": new_class.strip(),
                            "criteria": final_rubric  # חשוב: להשאיר keys לפי השרת
                        }
                        try:
                            if mode_en == "Create New Assignment":
                                res = requests.post(f"{API_URL}/teacher/rubrics", json=rubric_payload, timeout=60)
                            else:
                                res = requests.put(f"{API_URL}/teacher/rubrics/{target_id}", json=rubric_payload, timeout=60)
                            res.raise_for_status()
                            st.success("נשמר בהצלחה ✅")
                            time.sleep(1.2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ שמירה נכשלה: {e}")

            if mode_en == "Edit Existing Assignment" and target_id:
                with c_btn2:
                    if st.button("🗑️ מחיקת מטלה", type="primary"):
                        try:
                            res = requests.delete(f"{API_URL}/teacher/rubrics/{target_id}", timeout=60)
                            res.raise_for_status()
                            st.success("נמחק ✅")
                            time.sleep(1.2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ מחיקה נכשלה: {e}")

    # ========================================================
    # STUDENT DASHBOARD
    # ========================================================
    elif role == "student":
        st.title("הלוח שלי")
        student_class = user.get("class_name", "").strip()

        if not student_class:
            st.warning("⚠️ לא הוגדרה לך כיתה בפרופיל. לא יוצגו מטלות.")

        assigns = supabase.table("assignments").select("*").eq("class_name", student_class).execute().data
        subs = supabase.table("submissions").select("*").eq("student_id", user["id"]).execute().data
        sub_map = {s["assignment_id"]: s for s in subs}

        if not assigns and student_class:
            st.info(f"לא נמצאו מטלות לכיתה: '{student_class}'")

        for a in assigns:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(a["title"])
                s = sub_map.get(a["id"])

                if s:
                    c1.write(f"סטטוס: {he_status(s['status'])}")
                    if s["status"] == "Graded":
                        c2.metric("ציון", s["final_score"])
                        c1.success(s["feedback"])
                    else:
                        with c2.popover("עריכת קישור"):
                            l_edit = st.text_input("קישור חדש", value=s["link"], key=f"edit_{a['id']}")
                            if st.button("עדכון", key=f"update_{a['id']}"):
                                if not l_edit:
                                    st.error("אנא הזן/י קישור.")
                                elif not l_edit.startswith("https://scratch.mit.edu/projects/"):
                                    st.error("הקישור חייב להתחיל ב־ https://scratch.mit.edu/projects/")
                                else:
                                    try:
                                        project_id = l_edit.rstrip("/").split("/")[-1]
                                        check_resp = requests.get(
                                            f"https://api.scratch.mit.edu/projects/{project_id}",
                                            timeout=5
                                        )
                                        if check_resp.status_code == 200:
                                            supabase.table("submissions").update({"link": l_edit}).eq("id", s["id"]).execute()
                                            st.success("עודכן ✅")
                                            st.rerun()
                                        else:
                                            st.error("הפרויקט לא קיים או לא שותף (בדיקת API נכשלה).")
                                    except Exception as e:
                                        st.error(f"❌ שגיאה בבדיקת קישור: {e}")

                else:
                    c1.info("לא הוגש")
                    with c2.popover("הגשה"):
                        l = st.text_input("קישור", key=a["id"])
                        if st.button("שליחה", key=f"b_{a['id']}"):
                            if not l:
                                st.error("אנא הזן/י קישור.")
                            elif not l.startswith("https://scratch.mit.edu/projects/"):
                                st.error("הקישור חייב להתחיל ב־ https://scratch.mit.edu/projects/")
                            else:
                                try:
                                    project_id = l.rstrip("/").split("/")[-1]
                                    check_resp = requests.get(
                                        f"https://api.scratch.mit.edu/projects/{project_id}",
                                        timeout=5
                                    )
                                    if check_resp.status_code == 200:
                                        requests.post(
                                            f"{API_URL}/student/submit",
                                            json={"student_id": user["id"], "assignment_id": a["id"], "link": l},
                                            timeout=60
                                        )
                                        st.success("נשלח ✅")
                                        st.rerun()
                                    else:
                                        st.error("הפרויקט לא קיים או לא שותף (בדיקת API נכשלה).")
                                except Exception as e:
                                    st.error(f"❌ שגיאה: {e}")

    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================
    elif role == "admin":
        st.title("לוח מנהל/ת")

        users_data = supabase.table("users").select("*").execute().data
        assignments_data = supabase.table("assignments").select("*").execute().data
        submissions_data = supabase.table("submissions").select("*").execute().data

        graded_count = len([s for s in submissions_data if s["status"] == "Graded"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("תלמידים", len([u for u in users_data if u["role"] == "student"]))
        m2.metric("מורים", len([u for u in users_data if u["role"] == "teacher"]))
        m3.metric("מטלות", len(assignments_data) if assignments_data else 0)
        m4.metric("הגשות", len(submissions_data), f"{graded_count} נבדקו")

        st.divider()

        c_chart1, c_chart2 = st.columns(2)

        with c_chart1:
            st.subheader("📊 ביצועי כיתות")
            if assignments_data and submissions_data:
                assign_class_map = {a["id"]: a["class_name"] for a in assignments_data}
                class_grades = {}
                for s in submissions_data:
                    aid = s["assignment_id"]
                    if aid in assign_class_map and s.get("final_score") is not None:
                        cname = assign_class_map[aid]
                        class_grades.setdefault(cname, []).append(s["final_score"])

                avg_data = {"כיתה": [], "ממוצע ציון": []}
                for cname, grades in class_grades.items():
                    avg_data["כיתה"].append(cname)
                    avg_data["ממוצע ציון"].append(sum(grades) / len(grades))

                if avg_data["כיתה"]:
                    st.bar_chart(pd.DataFrame(avg_data).set_index("כיתה"))
                else:
                    st.info("אין עדיין הגשות שנבדקו.")
            else:
                st.info("אין מספיק נתונים.")

        with c_chart2:
            st.subheader("📌 סטטוס הגשות")
            if submissions_data:
                status_counts = pd.Series([he_status(s["status"]) for s in submissions_data]).value_counts()
                st.bar_chart(status_counts)
            else:
                st.info("אין הגשות.")

        st.divider()

        st.subheader("📋 סטטיסטיקה מפורטת למטלות")
        if assignments_data:
            stats_data = []
            for a in assignments_data:
                these_subs = [s for s in submissions_data if s["assignment_id"] == a["id"]]
                graded_subs = [s["final_score"] for s in these_subs if s.get("final_score") is not None]
                avg_grade = sum(graded_subs) / len(graded_subs) if graded_subs else 0

                stats_data.append({
                    "כיתה": a["class_name"],
                    "מטלה": a["title"],
                    "מספר הגשות": len(these_subs),
                    "ממוצע": f"{avg_grade:.1f}"
                })
            st.dataframe(pd.DataFrame(stats_data), width='stretch', hide_index=True)

        with st.expander("🏆 תלמידים מצטיינים"):
            if users_data and submissions_data:
                student_map = {u["id"]: u.get("full_name", u["username"]) for u in users_data if u["role"] == "student"}
                student_grades = {}
                for s in submissions_data:
                    sid = s["student_id"]
                    if sid in student_map and s.get("final_score") is not None:
                        student_grades.setdefault(sid, []).append(s["final_score"])

                leaderboard = []
                for sid, grades in student_grades.items():
                    leaderboard.append({
                        "תלמיד/ה": student_map[sid],
                        "ממוצע ציון": sum(grades) / len(grades),
                        "מספר פרויקטים": len(grades)
                    })

                if leaderboard:
                    df_leader = pd.DataFrame(leaderboard).sort_values("ממוצע ציון", ascending=False)
                    st.dataframe(df_leader, width='stretch', hide_index=True)
                else:
                    st.info("אין עדיין תלמידים עם ציונים.")

        st.divider()

        st.subheader("יצירת משתמש חדש")
        with st.form("create_user_form"):
            c1, c2 = st.columns(2)
            new_username = c1.text_input("שם משתמש")
            new_password = c2.text_input("סיסמה", type="password")
            new_fullname = c1.text_input("שם מלא")
            new_role = c2.selectbox("תפקיד", ["student", "teacher", "admin"], format_func=he_role)
            new_class = st.text_input("שם כיתה") if new_role == "student" else ""

            if st.form_submit_button("יצירה"):
                if new_username and new_password:
                    try:
                        user_payload = {
                            "username": new_username,
                            "password": new_password,
                            "full_name": new_fullname,
                            "role": new_role,
                            "class_name": new_class.strip() if new_role == "student" else None
                        }
                        supabase.table("users").insert(user_payload).execute()
                        st.success(f"המשתמש '{new_username}' נוצר ✅")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ שגיאה: {e}")
                else:
                    st.error("אנא מלא/י שם משתמש וסיסמה.")

        if users_data:
            df = pd.DataFrame(users_data)
            cols = ["username", "role", "full_name", "class_name", "password"]
            st.dataframe(df[[c for c in cols if c in df.columns]], width='stretch', hide_index=True)

        # ====================================================
        # BULK LOAD TEACHERS (CSV) - מהקוד האנגלי, עם עברית
        # ====================================================
        st.subheader("טעינה מרוכזת של מורים")
        with st.expander("📤 העלאת מורים מקובץ CSV"):
            st.write("העלה/י קובץ CSV עם כותרות: `username`, `password`, `full_name`")
            teacher_csv = st.file_uploader("בחר/י קובץ CSV", type="csv", key="teacher_upload")

            if teacher_csv is not None:
                if st.button("עיבוד והעלאה"):
                    try:
                        df_csv = pd.read_csv(teacher_csv)

                        required_cols = ["username", "password"]
                        if not all(col in df_csv.columns for col in required_cols):
                            st.error(f"CSV חייב להכיל לפחות: {required_cols}")
                        else:
                            success_count = 0
                            for _, row in df_csv.iterrows():
                                payload = {
                                    "username": str(row["username"]).strip(),
                                    "password": str(row["password"]).strip(),
                                    "full_name": str(row.get("full_name", "")).strip(),
                                    "role": "teacher",
                                    "class_name": None
                                }
                                supabase.table("users").insert(payload).execute()
                                success_count += 1

                            st.success(f"הועלו בהצלחה {success_count} מורים ✅")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ נכשל עיבוד הקובץ: {e}")