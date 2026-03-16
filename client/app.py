import json
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from supabase import create_client

from api.client import API_URL

ROOT = Path(__file__).parent
LOGO = ROOT / "assets" / "logo_without_back.png"

st.set_page_config(
    page_title="Scratch AI",
    page_icon=str(LOGO),
    layout="wide",
    initial_sidebar_state="expanded",
)
import base64


def centered_title_with_logo(title: str, logo_path: Path, img_px: int = 90, font_px: int = 54, gap_px: int = 12):
    b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:{gap_px}px;
            margin: 10px 0 8px 0;
        ">
            <span style="
                font-size:{font_px}px;
                font-weight:800;
                line-height:1;
                margin:0;
            ">{title}</span>
            <img src="data:image/png;base64,{b64}" style="width:{img_px}px; height:auto;" />
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# CONFIGURATION
# Put these in .streamlit/secrets.toml (recommended) like:
# SUPABASE_URL="https://xxxx.supabase.co"
# SUPABASE_KEY="YOUR_KEY"
# ============================================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://hmouoztlgrsotauzohgm.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")  # <-- DO NOT hardcode secrets in code

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
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Debug: SUPABASE_URL or SUPABASE_KEY is empty string.")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Debug: Error connecting to Supabase: {e}")
        return None


def navigate(page: str):
    st.session_state.page = page
    st.session_state["_hard_clear"] = True  # <-- forces immediate UI clear on next rerun
    st.rerun()


def logout():
    st.session_state.auth_user = None
    st.session_state["logged_in"] = False
    navigate("home")


@st.cache_data(ttl=20, show_spinner=False)
def fetch_users():
    sb = init_supabase()
    if sb is None:
        return []
    return sb.table("users").select("id, username, role, full_name, class_name, school_id").execute().data or []


@st.cache_data(ttl=20, show_spinner=False)
def fetch_assignments():
    sb = init_supabase()
    if sb is None:
        return []

    data = (
            sb.table("assignments")
            .select("id, title, class_name, teacher_id, rubric")  # ✅ removed criteria
            .execute()
            .data
            or []
    )

    # Backward-compat: let the rest of the app keep using a["criteria"]
    for a in data:
        if "criteria" not in a:
            a["criteria"] = a.get("rubric")

    return data


@st.cache_data(ttl=20, show_spinner=False)
def fetch_submissions():
    sb = init_supabase()
    if sb is None:
        return []
    return sb.table("submissions").select(
        "id, assignment_id, student_id, status, final_score, link, feedback").execute().data or []


# ============================================================
# ROOT UI CONTAINER (prevents page-mixing during reruns)
# ============================================================
if "_hard_clear" not in st.session_state:
    st.session_state["_hard_clear"] = False

APP = st.empty()

# If we navigated, clear previous UI immediately
if st.session_state["_hard_clear"]:
    APP.empty()
    st.session_state["_hard_clear"] = False

# ============================================================
# APP (everything UI must be inside APP.container())
# ============================================================
with APP.container():
    load_css()
    supabase = init_supabase()

    if supabase is None:
        st.error("❌ אין חיבור ל-Supabase. ודא/י שהגדרת SUPABASE_URL ו-SUPABASE_KEY ב-secrets.toml.")
        st.stop()

    # Session init
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "target" not in st.session_state:
        st.session_state.target = None
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    # ============================================================
    # PAGE: HOME
    # ============================================================
    if st.session_state.page == "home":
        centered_title_with_logo("Scratch AI", LOGO, img_px=95, font_px=56, gap_px=10)
        st.divider()

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("""<div class="role-card"><h1>👨‍🎓</h1><h3>תלמיד/ה</h3></div>""", unsafe_allow_html=True)
            if not st.session_state["logged_in"]:
                if st.button("התחברות תלמיד/ה", width="stretch"):
                    st.session_state.target = "student"
                    navigate("login")

        with c2:
            st.markdown("""<div class="role-card"><h1>🏫</h1><h3>מורה</h3></div>""", unsafe_allow_html=True)
            if not st.session_state["logged_in"]:
                if st.button("התחברות מורה", width="stretch"):
                    st.session_state.target = "teacher"
                    navigate("login")

        with c3:
            st.markdown("""<div class="role-card"><h1>🛡️</h1><h3>מנהל/ת</h3></div>""", unsafe_allow_html=True)
            if not st.session_state["logged_in"]:
                if st.button("התחברות מנהל/ת", width="stretch"):
                    st.session_state.target = "admin"
                    navigate("login")

    # ============================================================
    # PAGE: LOGIN
    # ============================================================
    elif st.session_state.page == "login":
        tgt = st.session_state.target

        c1, c2, c3 = st.columns([1, 2, 1])

        with c2:
            if not st.session_state["logged_in"]:
                with st.form("login"):
                    st.markdown(
                        f"<h3 style='text-align: center;'>התחברות {he_role(tgt)}</h3>",
                        unsafe_allow_html=True)

                    u = st.text_input("שם משתמש").strip()
                    p = st.text_input("סיסמה", type="password").strip()

                    c_name = ""
                    if tgt == "student":
                        c_name = st.text_input("שם כיתה").strip()
                        st.caption("טיפ: אם אין לך משתמש, החשבון ייווצר אוטומטית אם הכיתה קיימת.")

                    submitted = st.form_submit_button("כניסה", width="stretch")

                    if submitted:
                        if not u or not p:
                            st.error("אנא הזן/י שם משתמש וסיסמה.")
                            st.stop()

                        # חיפוש משתמש קיים לפי username
                        res = supabase.table("users").select("*, schools(name)").eq("username", u).execute()
                        found_user = res.data[0] if res.data else None

                        if found_user:
                            if tgt == "student":
                                if found_user.get("class_name") != c_name:
                                    st.error(
                                        f"⛔ אין הרשאה: אתה רשום/ה לכיתה '{found_user.get('class_name')}', לא '{c_name}'."
                                    )
                                elif str(found_user.get("password", "")) == p:
                                    st.session_state.auth_user = found_user
                                    st.session_state["logged_in"] = True
                                    navigate("dashboard")
                                else:
                                    st.error("סיסמה שגויה.")
                            else:
                                # מורה/מנהל
                                if str(found_user.get("password", "")) == p:
                                    st.session_state.auth_user = found_user
                                    st.session_state["logged_in"] = True
                                    navigate("dashboard")
                                else:
                                    st.error("סיסמה שגויה.")


                        elif tgt == "student":

                            # רישום אוטומטי לתלמיד חדש

                            if not c_name:
                                st.error("שם כיתה הוא חובה לתלמיד חדש.")

                            else:
                                # נחפש את הכיתה וגם מי המורה שלה כדי לרשת את בית הספר
                                class_check = (
                                    supabase.table("assignments")
                                    .select("class_name, teacher_id")
                                    .eq("class_name", c_name)
                                    .execute()

                                )

                                if not class_check.data:

                                    st.error(f"הכיתה '{c_name}' לא קיימת. פנה/י למורה.")

                                else:

                                    try:

                                        # חילוץ מזהה המורה ומשיכת בית הספר שלו

                                        teacher_id = class_check.data[0].get("teacher_id")

                                        teacher_res = supabase.table("users").select("school_id").eq("id",
                                                                                                     teacher_id).execute()

                                        school_id = teacher_res.data[0].get("school_id") if teacher_res.data else None

                                        new_student = {

                                            "username": u,

                                            "password": p,

                                            "role": "student",

                                            "full_name": u,

                                            "class_name": c_name,

                                            "school_id": school_id

                                        }

                                        # 1. הוספת התלמיד (בלי select בסוף!)

                                        insert_res = supabase.table("users").insert(new_student).execute()

                                        if insert_res.data:

                                            # 2. שליפה מחדש של התלמיד יחד עם שם בית הספר להתחברות

                                            new_user_id = insert_res.data[0]["id"]

                                            full_user_res = supabase.table("users").select("*, schools(name)").eq("id",
                                                                                                                  new_user_id).execute()

                                            st.success(f"ברוך/ה הבא/ה! נוצר חשבון עבור {u} בכיתה {c_name}.")

                                            st.session_state.auth_user = full_user_res.data[
                                                0] if full_user_res.data else insert_res.data[0]

                                            st.session_state["logged_in"] = True

                                            navigate("dashboard")

                                        else:

                                            st.error("נכשלה יצירת משתמש (לא הוחזרו נתונים).")

                                    except Exception as e:

                                        st.error(f"❌ שגיאה ביצירת חשבון: {e}")

        if st.button("חזרה"):
            navigate("home")

    # ============================================================
    # PAGE: DASHBOARD
    # ============================================================
    elif st.session_state.page == "dashboard":
        user = st.session_state.auth_user
        if not user:
            navigate("home")

        role = user.get("role", "")

        # nicer loading feel when dashboard is heavy
        with st.spinner("טוען לוח..."):
            pass

        col1, col2, col3 = st.columns([6, 4, 3])

        with col3:
            name = user.get('full_name', user.get('username', ''))
            school_data = user.get("schools")
            school_name = school_data.get("name") if isinstance(school_data, dict) else ""

            if school_name:
                st.markdown(
                    f"""
                                <div style="display: flex; align-items: baseline; gap: 10px;">
                                    <h1 style="margin: 0;">👤 {name}</h1>
                                    <span style="color: #666; font-size: 18px;">🏫 {school_name}</span>
                                </div>
                                """,
                    unsafe_allow_html=True
                )
            else:
                st.title(f"👤 {name}")

        with col1:
            if st.button("התנתקות"):
                logout()

        # ========================================================
        # TEACHER DASHBOARD
        # ========================================================
        if role == "teacher" and st.session_state["logged_in"]:
            st.title("לוח מורה")
            tab1, tab2, tab3 = st.tabs(["בדיקת עבודות", "ניהול מטלות", "ניהול תלמידים"])
            # ----------------------------
            # TAB 1: GRADING
            # ----------------------------
            with tab1:
                st.subheader("הגשות תלמידים")

                teacher_assigns = (
                        supabase.table("assignments")
                        .select("*")
                        .eq("teacher_id", user["id"])
                        .execute()
                        .data
                        or []
                )
                teacher_classes = sorted(list({a.get("class_name") for a in teacher_assigns if a.get("class_name")}))
                students_rows = []
                if teacher_classes:
                    students_rows = (
                            supabase.table("users")
                            .select("id, full_name, username, class_name")
                            .eq("role", "student")
                            .in_("class_name", teacher_classes)
                            .execute()
                            .data
                            or []
                    )

                all_assigns = {a["id"]: a for a in teacher_assigns}
                teacher_assign_ids = list(all_assigns.keys())

                if not teacher_assign_ids:
                    st.info("אין לך עדיין מטלות. צור/י מטלה כדי לראות הגשות.")
                else:
                    all_subs = (
                            supabase.table("submissions")
                            .select("*")
                            .in_("assignment_id", teacher_assign_ids)
                            .execute()
                            .data
                            or []
                    )

                    if not all_subs:
                        st.info("אין עדיין הגשות למטלות שלך.")
                    else:
                        student_ids = sorted(list({s["student_id"] for s in all_subs}))
                        users_rows = (
                                supabase.table("users")
                                .select("id, full_name, username")
                                .in_("id", student_ids)
                                .execute()
                                .data
                                or []
                        )

                        all_users = {
                            u["id"]: u.get("full_name", u.get("username", "לא ידוע/ה"))
                            for u in users_rows
                        }

                        filtered_subs = all_subs

                        filter_mode_en = st.radio(
                            "סינון לפי",
                            ["All", "Student", "Assignment"],
                            horizontal=True,
                            format_func=lambda x: FILTER_MODE_HE.get(x, x),
                        )

                        if filter_mode_en == "Student":
                            selected_student = st.selectbox(
                                "בחר/י תלמיד/ה",
                                student_ids,
                                format_func=lambda x: all_users.get(x, "לא ידוע/ה"),
                            )
                            filtered_subs = [s for s in all_subs if s["student_id"] == selected_student]

                        elif filter_mode_en == "Assignment":
                            assign_ids = sorted(
                                list({s["assignment_id"] for s in all_subs}),
                                key=lambda x: all_assigns.get(x, {}).get("title", "מטלה לא ידועה"),
                            )
                            selected_assign = st.selectbox(
                                "בחר/י מטלה",
                                assign_ids,
                                format_func=lambda x: all_assigns.get(x, {}).get("title", "מטלה לא ידועה"),
                            )
                            filtered_subs = [s for s in all_subs if s["assignment_id"] == selected_assign]

                        for s in filtered_subs:
                            s_name = all_users.get(s["student_id"], "תלמיד/ה לא ידוע/ה")
                            assignment_data = all_assigns.get(s["assignment_id"], {})
                            a_title = assignment_data.get("title", "מטלה לא ידועה")
                            rubric_to_send = assignment_data.get("criteria", [])

                            with st.expander(f"{s_name} - {a_title}"):
                                st.write(f"קישור: {s.get('link', '')}")

                                if st.button("🤖 ניתוח עם AI", key=f"ai_{s['id']}"):
                                    with st.spinner("מנתח פרויקט עם AI ו-Dr. Scratch..."):
                                        try:
                                            payload = {"project_url": s["link"], "rubrics": rubric_to_send}
                                            response = requests.post(
                                                f"{API_URL}/teacher/analyze_ai",
                                                json=payload,
                                                timeout=120,
                                            )
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
                                        value=int(st.session_state.get(f"sc_{s['id']}", 0)),
                                    )

                                    fb = st.text_area(
                                        "משוב סופי",
                                        value=st.session_state.get(f"fb_{s['id']}", ""),
                                        height=200,
                                    )

                                    if st.form_submit_button("שמירת ציון"):
                                        try:
                                            supabase.table("submissions").update(
                                                {"final_score": score, "feedback": fb, "status": "Graded"}
                                            ).eq("id", s["id"]).execute()

                                            st.success(f"הציון עבור {s_name} נשמר ✅")
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
                    format_func=lambda x: MODE_HE.get(x, x),
                )

                current_rubric_data = [
                    {
                        "name": "קוד ואלגוריתמיקה",
                        "weight": 40,
                        "sub_criteria": [
                            {"name": "כמות אובייקטים פעילים", "weight": 12},
                            {"name": "שימוש באמצעי קלט וחיישנים", "weight": 12},
                            {"name": "אירועים ומסרים בין דמויות", "weight": 15},
                            {"name": "תנאים, לולאות ותגובתיות", "weight": 25},
                            {"name": "שימוש במשתנים ואיפוס נכון", "weight": 20},
                            {"name": "סדר וארגון הקוד (יעילות)", "weight": 16},
                        ],
                    },
                    {
                        "name": "עיצוב וחוויית משתמש",
                        "weight": 30,
                        "sub_criteria": [
                            {"name": "נוחות השימוש וזרימת המשחק", "weight": 25},
                            {"name": "עיצוב דמויות ורקעים", "weight": 25},
                            {"name": "שילוב סאונד ואפקטים", "weight": 25},
                            {"name": "הוראות ברורות ותפריטים", "weight": 25},
                        ],
                    },
                    {
                        "name": "יצירתיות ומחשבה אישית",
                        "weight": 30,
                        "sub_criteria": [
                            {"name": "חדשנות ומקוריות ברעיון", "weight": 40},
                            {"name": "עקביות ומטרת פרויקט ברורה", "weight": 30},
                            {"name": "פתרונות חכמים לבעיות", "weight": 30},
                        ],
                    },
                ]

                title_val = ""
                class_val = ""
                target_id = None

                if mode_en == "Edit Existing Assignment":
                    assigns = supabase.table("assignments").select("*").eq("teacher_id", user["id"]).execute().data
                    if assigns:
                        opts = {f"{a['title']} ({a['class_name']})": a for a in assigns}
                        sel = st.selectbox("בחר/י מטלה", list(opts.keys()))
                        target_a = opts[sel]

                        title_val = target_a["title"]
                        class_val = target_a["class_name"]
                        target_id = target_a["id"]

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
                cols = st.columns(3)

                for i in range(3):
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

                        df_subs = pd.DataFrame(subs)
                        if "name" not in df_subs.columns or "weight" not in df_subs.columns:
                            df_subs = pd.DataFrame(columns=["name", "weight"])

                        st.caption("תתי־קריטריונים")

                        edited_df = st.data_editor(
                            df_subs,
                            key=f"ed_{i}",
                            hide_index=True,
                            width="stretch",
                            num_rows="fixed",
                            disabled=["name"],
                            column_config={
                                "name": st.column_config.TextColumn("שם קריטריון", required=True),
                                "weight": st.column_config.NumberColumn(
                                    "משקל", min_value=0, max_value=100, required=True
                                ),
                            },
                        )

                        sub_sum = edited_df["weight"].sum() if "weight" in edited_df.columns else 0

                        if sub_sum != 100:
                            st.error(f"סכום תתי־קריטריונים: {sub_sum}%")
                            all_subs_valid = False
                        else:
                            st.success("סכום תתי־קריטריונים: 100% ✅")

                        final_rubric.append(
                            {"name": cat_name, "weight": w, "sub_criteria": edited_df.to_dict(orient="records")}
                        )

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
                    if st.button(btn_text, width="stretch"):
                        if not main_valid or not all_subs_valid or not new_class.strip():
                            st.error("אנא תקן/י את השגיאות למעלה וודא/י ששדה כיתה אינו ריק.")
                        else:
                            rubric_payload = {
                                "teacher_id": user["id"],
                                "title": new_title,
                                "class_name": new_class.strip(),
                                "criteria": final_rubric,
                            }
                            try:
                                payload_bytes = json.dumps(rubric_payload, ensure_ascii=False).encode("utf-8")
                                headers = {"Content-Type": "application/json; charset=utf-8"}

                                if mode_en == "Create New Assignment":
                                    res = requests.post(
                                        f"{API_URL}/teacher/rubrics",
                                        data=payload_bytes,
                                        headers=headers,
                                        timeout=60
                                    )
                                else:
                                    res = requests.put(
                                        f"{API_URL}/teacher/rubrics/{target_id}",
                                        data=payload_bytes,
                                        headers=headers,
                                        timeout=60
                                    )
                                res.raise_for_status()
                                st.success("נשמר בהצלחה ✅")
                                time.sleep(1.2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ שמירה נכשלה: {e}")

                if mode_en == "Edit Existing Assignment" and target_id:
                    with c_btn2:
                        if st.button("🗑️ מחיקת מטלה", type="primary", width="stretch"):
                            try:
                                res = requests.delete(f"{API_URL}/teacher/rubrics/{target_id}", timeout=60)
                                res.raise_for_status()
                                st.success("נמחק ✅")
                                time.sleep(1.2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ מחיקה נכשלה: {e}")
            # ----------------------------
            # TAB 3: MANAGE STUDENTS
            # ----------------------------
            with tab3:
                st.subheader("ניהול תלמידים")

                with st.expander("📤 העלאת תלמידים מקובץ CSV"):
                    st.write("העלה/י קובץ CSV עם כותרות: `username`, `password`, `full_name`")

                    # משיכת המזהה של בית הספר של המורה כדי להוריש אותו לתלמידים
                    teacher_school_id = user.get("school_id")

                    batch_class = st.text_input("לאיזו כיתה לשייך תלמידים אלו?", key="teacher_csv_class")

                    students_csv = st.file_uploader("בחר/י קובץ CSV", type="csv",
                                                    key="students_upload_teacher")

                    if students_csv is not None:
                        if st.button("עיבוד והעלאה לתלמידים", width="stretch"):
                            if not batch_class.strip():
                                st.error("חובה להזין שם כיתה עבור התלמידים.")
                            else:
                                try:
                                    df_csv = pd.read_csv(students_csv)
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
                                                "role": "student",
                                                "class_name": batch_class.strip(),
                                                "school_id": teacher_school_id,
                                            }
                                            supabase.table("users").insert(payload).execute()
                                            success_count += 1

                                        st.success(
                                            f"הועלו בהצלחה {success_count} תלמידים לכיתה {batch_class} ✅")
                                        time.sleep(1)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ נכשל עיבוד הקובץ: {e}")

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
                            c1.success(s.get("feedback", ""))
                        else:
                            with c2.popover("עריכת קישור"):
                                l_edit = st.text_input("קישור חדש", value=s["link"], key=f"edit_{a['id']}")
                                if st.button("עדכון", key=f"update_{a['id']}", width="stretch"):
                                    if not l_edit:
                                        st.error("אנא הזן/י קישור.")
                                    elif not l_edit.startswith("https://scratch.mit.edu/projects/"):
                                        st.error("הקישור חייב להתחיל ב־ https://scratch.mit.edu/projects/")
                                    else:
                                        try:
                                            project_id = l_edit.rstrip("/").split("/")[-1]
                                            check_resp = requests.get(
                                                f"https://api.scratch.mit.edu/projects/{project_id}", timeout=5
                                            )
                                            if check_resp.status_code == 200:
                                                supabase.table("submissions").update({"link": l_edit}).eq(
                                                    "id", s["id"]
                                                ).execute()
                                                st.success("עודכן ✅")
                                                st.rerun()
                                            else:
                                                st.error("הפרויקט לא קיים או לא שותף (בדיקת API נכשלה).")
                                        except Exception as e:
                                            st.error(f"❌ שגיאה בבדיקת קישור: {e}")

                    else:
                        c1.info("לא הוגש")
                        with c2.popover("הגשה"):
                            l = st.text_input("קישור", key=str(a["id"]))
                            if st.button("שליחה", key=f"b_{a['id']}", width="stretch"):
                                if not l:
                                    st.error("אנא הזן/י קישור.")
                                elif not l.startswith("https://scratch.mit.edu/projects/"):
                                    st.error("הקישור חייב להתחיל ב־ https://scratch.mit.edu/projects/")
                                else:
                                    try:
                                        project_id = l.rstrip("/").split("/")[-1]
                                        check_resp = requests.get(
                                            f"https://api.scratch.mit.edu/projects/{project_id}", timeout=5
                                        )
                                        if check_resp.status_code == 200:
                                            requests.post(
                                                f"{API_URL}/student/submit",
                                                json={"student_id": user["id"], "assignment_id": a["id"], "link": l},
                                                timeout=60,
                                            )
                                            st.success("נשלח ✅")
                                            st.rerun()
                                        else:
                                            st.error("הפרויקט לא קיים או לא שותף (בדיקת API נכשלה).")
                                    except Exception as e:
                                        st.error(f"❌ שגיאה: {e}")

                    with st.expander("📊 צפייה במחוון (קריטריונים לציון)"):
                        criteria = a.get("rubric") or a.get("criteria")
                        if not criteria or not isinstance(criteria, list):
                            st.info("לא הוגדר מחוון למטלה זו.")
                        else:
                            for cat in criteria:
                                if not isinstance(cat, dict):
                                    continue
                                c_name = cat.get("name", "קטגוריה")
                                c_weight = cat.get("weight", 0)
                                st.markdown(f"**{c_name} ({c_weight}%)**")
                                subs2 = cat.get("sub_criteria", [])
                                if subs2:
                                    for sub in subs2:
                                        if isinstance(sub, dict):
                                            s_name = sub.get("name", "")
                                            s_weight = sub.get("weight", 0)
                                            st.markdown(f"- {s_name} ({s_weight}%)")
                                        else:
                                            st.markdown(f"- {sub}")

        # ========================================================
        # ADMIN DASHBOARD
        # ========================================================
        elif role == "admin":
            st.title("לוח מנהל/ת")

            # בדיקה האם מדובר במנהל בית ספר ספציפי או במנהל רשת (Super Admin)
            admin_school_id = user.get("school_id")

            with st.spinner("טוען נתונים..."):
                all_users_data = fetch_users()
                all_assignments_data = fetch_assignments()
                all_submissions_data = fetch_submissions()
                all_schools_data = supabase.table("schools").select("*").execute().data or []

                # סינון נתונים אם מדובר במנהל בית ספר
                if admin_school_id:
                    users_data = [u for u in all_users_data if u.get("school_id") == admin_school_id]
                    schools_data = [s for s in all_schools_data if s["id"] == admin_school_id]

                    # חילוץ מזהי המורים והתלמידים של בית הספר
                    teacher_ids = {u["id"] for u in users_data if u["role"] == "teacher"}
                    student_ids = {u["id"] for u in users_data if u["role"] == "student"}

                    # מטלות ששייכות למורים בבית הספר והגשות של תלמידים בבית הספר
                    assignments_data = [a for a in all_assignments_data if a.get("teacher_id") in teacher_ids]
                    submissions_data = [s for s in all_submissions_data if s.get("student_id") in student_ids]
                else:
                    # Super Admin רואה הכל
                    users_data = all_users_data
                    schools_data = all_schools_data
                    assignments_data = all_assignments_data
                    submissions_data = all_submissions_data

                school_options = {s["name"]: s["id"] for s in schools_data}

            graded_count = len([s for s in submissions_data if s["status"] == "Graded"])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("תלמידים", len([u for u in users_data if u["role"] == "student"]))
            m2.metric("מורים", len([u for u in users_data if u["role"] == "teacher"]))
            m3.metric("מטלות", len(assignments_data) if assignments_data else 0)
            m4.metric("הגשות", len(submissions_data), f"{graded_count} נבדקו")

            st.divider()

            # מנהל רשת רואה לשונית בתי ספר, מנהל בית ספר לא
            if not admin_school_id:
                tab_stats, tab_members, tab_schools = st.tabs(
                    ["📊 סטטיסטיקה", "👥 ניהול והוספת משתמשים", "🏫 ניהול בתי ספר"])
            else:
                tab_stats, tab_members = st.tabs(["📊 סטטיסטיקה", "👥 ניהול והוספת משתמשים"])

            # ----------------------------
            # TAB 1: STATISTICS
            # ----------------------------
            with tab_stats:
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

                        stats_data.append(
                            {
                                "כיתה": a["class_name"],
                                "מטלה": a["title"],
                                "מספר הגשות": len(these_subs),
                                "ממוצע": f"{avg_grade:.1f}",
                            }
                        )

                    df_stats = pd.DataFrame(stats_data)
                    st.table(df_stats)

                with st.expander("🏆 תלמידים מצטיינים"):
                    if users_data and submissions_data:
                        student_map = {
                            u["id"]: u.get("full_name", u["username"]) for u in users_data if u["role"] == "student"
                        }
                        student_grades = {}
                        for s in submissions_data:
                            sid = s["student_id"]
                            if sid in student_map and s.get("final_score") is not None:
                                student_grades.setdefault(sid, []).append(s["final_score"])

                        leaderboard = []
                        for sid, grades in student_grades.items():
                            leaderboard.append(
                                {"תלמיד/ה": student_map[sid], "ממוצע ציון": (sum(grades) / len(grades)),
                                 "מספר פרויקטים": len(grades)}
                            )

                        if leaderboard:
                            df_leader = (
                                pd.DataFrame(leaderboard).sort_values("ממוצע ציון", ascending=False).reset_index(
                                    drop=True)
                            )
                            st.table(df_leader.style.format({"ממוצע ציון": "{:.2f}"}))
                        else:
                            st.info("אין עדיין תלמידים עם ציונים.")

            # ----------------------------
            # TAB 2: MEMBERS (MANUAL & CSV)
            # ----------------------------
            with tab_members:
                st.subheader("יצירת משתמש חדש")
                with st.form("create_user_form"):
                    c1, c2 = st.columns(2)
                    new_username = c1.text_input("שם משתמש")
                    new_password = c2.text_input("סיסמה", type="password")
                    new_fullname = c1.text_input("שם מלא")
                    new_role = c2.selectbox("תפקיד", ["student", "teacher", "admin"], format_func=he_role)
                    new_class = st.text_input("שם כיתה") if new_role == "student" else ""

                    if admin_school_id:
                        selected_school_id = admin_school_id
                    else:
                        selected_school_name = st.selectbox("שיוך לבית ספר", list(school_options.keys()))
                        selected_school_id = school_options.get(
                            selected_school_name) if selected_school_name else None

                    if st.form_submit_button("יצירה"):
                        if new_username and new_password:
                            try:
                                user_payload = {
                                    "username": new_username,
                                    "password": new_password,
                                    "full_name": new_fullname,
                                    "role": new_role,
                                    "class_name": new_class.strip() if new_role == "student" else None,
                                    "school_id": selected_school_id
                                }
                                supabase.table("users").insert(user_payload).execute()
                                st.success(f"המשתמש '{new_username}' נוצר ✅")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ שגיאה: {e}")
                        else:
                            st.error("אנא מלא/י שם משתמש וסיסמה.")

                st.divider()

                st.subheader("טעינה מרוכזת מקובץ CSV")
                with st.expander("📤 העלאת משתמשים מקובץ CSV"):
                    st.write("העלה/י קובץ CSV עם כותרות: `username`, `password`, `full_name`")

                    batch_role = st.selectbox("סוג משתמשים בקובץ", ["teacher", "student"], format_func=he_role,
                                              key="csv_role")

                    batch_class = ""
                    if batch_role == "student":
                        batch_class = st.text_input("שם כיתה (עבור תלמידים אלו)", key="csv_class")

                    if admin_school_id:
                        batch_school_id = admin_school_id
                    else:
                        batch_school_name = st.selectbox("לאיזה בית ספר לשייך משתמשים אלו?",
                                                         list(school_options.keys()), key="csv_school")
                        batch_school_id = school_options.get(batch_school_name) if batch_school_name else None

                    users_csv = st.file_uploader("בחר/י קובץ CSV", type="csv", key="users_upload_admin")

                    if users_csv is not None:
                        if st.button("עיבוד והעלאה", width="stretch"):
                            if batch_role == "student" and not batch_class.strip():
                                st.error("חובה להזין שם כיתה עבור תלמידים.")
                            else:
                                try:
                                    df_csv = pd.read_csv(users_csv)
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
                                                "role": batch_role,
                                                "class_name": batch_class.strip() if batch_role == "student" else None,
                                                "school_id": batch_school_id,
                                            }
                                            supabase.table("users").insert(payload).execute()
                                            success_count += 1

                                        st.success(f"הועלו בהצלחה {success_count} {ROLE_HE.get(batch_role)} ✅")
                                        time.sleep(1)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ נכשל עיבוד הקובץ: {e}")

                st.divider()
                st.subheader("רשימת משתמשים")
                if users_data:
                    df_users = pd.DataFrame(users_data)
                    cols = ["username", "role", "full_name", "class_name"]
                    st.dataframe(df_users[[c for c in cols if c in df_users.columns]], width="stretch")

            # ----------------------------
            # TAB 3: SCHOOLS (Only for Super Admin)
            # ----------------------------
            if not admin_school_id:
                with tab_schools:
                    st.subheader("ניהול בתי ספר")
                    with st.form("create_school_form"):
                        new_school_name = st.text_input("שם בית הספר החדש")
                        if st.form_submit_button("הוספת בית ספר"):
                            if new_school_name.strip():
                                try:
                                    existing_school = supabase.table("schools").select("id").eq("name",
                                                                                                new_school_name.strip()).execute()
                                    if existing_school.data:
                                        st.error(f"בית הספר '{new_school_name.strip()}' כבר קיים במערכת.")
                                    else:
                                        supabase.table("schools").insert(
                                            {"name": new_school_name.strip()}).execute()
                                        st.success(f"בית הספר '{new_school_name.strip()}' נוסף בהצלחה ✅")
                                        time.sleep(1.2)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ שגיאה בהוספת בית ספר: {e}")
                            else:
                                st.error("אנא הזן/י את שם בית הספר.")

                    st.divider()
                    st.subheader("בתי ספר קיימים")
                    if schools_data:
                        df_schools = pd.DataFrame(schools_data)
                        st.dataframe(df_schools, width="stretch")
                    else:
                        st.info("אין עדיין בתי ספר במערכת.")

    else:
        st.warning("⚠️ לא נמצא תפקיד תקין למשתמש הזה.")
        if st.button("חזרה לדף הבית"):
            logout()
