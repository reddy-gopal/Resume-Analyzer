import streamlit as st
import pandas as pd
import plotly.express as px
from contextlib import contextmanager
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# --- Local Imports ---
from ai.parser import extract_text_from_pdf, extract_text_from_docx, clean_text
from ai.feedback import analyze_with_gemini
from backend.db import SessionLocal, init_db
from backend.models.evaluation import Evaluation

# --- Initialize Database ---
try:
    init_db()
except Exception as e:
    st.error(f"Failed to initialize database: {e}")

# --- Context Manager for DB Session ---
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Database Functions ---
def save_evaluation(result, resume_name, jd_content, username):
    with get_db_session() as db:
        new_evaluation = Evaluation(
            username=username,
            resume_filename=resume_name,
            job_description_summary=jd_content[:250] + "...",
            overall_score=result.get('overall_score'),
            matching_skills=result.get('matching_skills'),
            missing_skills=result.get('missing_skills'),
            feedback=result.get('feedback')
        )
        db.add(new_evaluation)
        db.commit()

def load_evaluations():
    with get_db_session() as db:
        evaluations = db.query(Evaluation).order_by(Evaluation.created_at.desc()).all()
        return pd.DataFrame([{'ID': e.id, 'User': e.username, 'Resume': e.resume_filename,
            'Score': e.overall_score, 'Matching Skills': ', '.join(e.matching_skills or []),
            'Missing Skills': ', '.join(e.missing_skills or []),
            'Date': e.created_at.strftime("%Y-%m-%d %H:%M")} for e in evaluations])

# --- UI Helper Functions ---
def get_file_text(uploaded_file):
    if uploaded_file.name.endswith(".pdf"): return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"): return extract_text_from_docx(uploaded_file)
    return uploaded_file.read().decode("utf-8")

def display_analysis_results(result, show_feedback=True):
    st.subheader("Analysis Report")
    score = result.get('overall_score', 0)
    matching = result.get('matching_skills', [])
    missing = result.get('missing_skills', [])
    feedback = result.get('feedback', "No feedback was generated.")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"**Overall Match Score**")
        fig = px.pie(values=[score, 100 - score], names=['Match', 'Gap'], hole=0.6,
                     color_discrete_map={'Match': '#28A745', 'Gap': '#33373B'})
        fig.update_traces(textinfo='none', showlegend=False)
        fig.add_annotation(text=f"<b>{score}%</b>", x=0.5, y=0.5, font_size=32, showarrow=False)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Skills Analysis**")
        if matching:
            st.markdown("<h6>Matching Skills</h6>", unsafe_allow_html=True)
            st.markdown(''.join([f'<span class="skill-tag-green">{skill}</span>' for skill in matching]), unsafe_allow_html=True)
        if missing:
            st.markdown("<h6 style='margin-top: 15px;'>Missing Skills</h6>", unsafe_allow_html=True)
            st.markdown(''.join([f'<span class="skill-tag-red">{skill}</span>' for skill in missing]), unsafe_allow_html=True)

    if show_feedback:
        st.divider()
        st.markdown("### 📝 Personalized AI Feedback")
        st.markdown(feedback)

# --- Page Configuration and Styling (Dark Theme) ---
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    /* Base */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    h1, h2, h3, h4, h5 {
        color: #FAFAFA !important;
    }
    .stTabs [data-baseweb="tab-list"] button {
        color: #C6C6C6;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #FFFFFF;
    }
    /* Skills */
    h6 { color: #A0A0A0; }
    .skill-tag-green, .skill-tag-red {
        display: inline-block;
        padding: 6px 12px;
        margin: 5px 5px 5px 0;
        border-radius: 15px;
        font-weight: 500;
        font-size: 14px;
        color: white;
    }
    .skill-tag-green { background-color: #28A745; }
    .skill-tag-red { background-color: #DC3545; }
</style>
""", unsafe_allow_html=True)

# --- USER AUTHENTICATION ---
with open('resume-matcher-project/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

st.title("🧠 AI Resume Analyzer")

# --- LOGIN SCREEN WITH DEMO CREDENTIALS ---
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    col1, col2 = st.columns([2,1.5])
    with col1:
        authenticator.login('main')
    with col2:
        st.subheader("Demo Credentials")
        st.info("""
        **Admin (Placement Team)**
        - **Username:** `admin`
        - **Password:** `abc123`

        **Employee / Student**
        - **Username:** `employee`
        - **Password:** `password`
        """)

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    name = st.session_state["name"]
    user_role = config['credentials']['usernames'][username]['role']
    
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.title(f"Welcome, {name}")
    st.sidebar.write(f"Role: **{user_role.capitalize()}**")

    # --- ROLE-BASED APP LAYOUT ---
    if user_role == 'admin':
        st.header("Placement Team Dashboard")
        tab1, tab2 = st.tabs(["📊 Dashboard", "🔬 Analyze a Resume"])
        
        with tab1:
            st.subheader("All Saved Evaluations")
            df_evals = load_evaluations()
            st.dataframe(df_evals, use_container_width=True, hide_index=True)
        
        with tab2:
            st.subheader("Analyze a Candidate Resume")
            jd_file = st.file_uploader("Upload Job Description", key="admin_jd")
            resume_file = st.file_uploader("Upload Candidate Resume", key="admin_resume")
            if st.button("Analyze", key="admin_analyze"):
                if not jd_file or not resume_file:
                    st.warning("Please upload both files.")
                else:
                    jd_content = get_file_text(jd_file)
                    resume_content = get_file_text(resume_file)
                    with st.spinner("Analyzing..."):
                        result = analyze_with_gemini(clean_text(resume_content), clean_text(jd_content))
                        if "error" in result:
                            st.error(result['error'])
                        else:
                            save_evaluation(result, resume_file.name, jd_content, username)
                            st.success("Analysis complete and saved to dashboard!")
                            display_analysis_results(result, show_feedback=False)

    elif user_role == 'employee':
        st.header("Improve Your Resume")
        jd_file = st.file_uploader("Upload the Job Description")
        resume_file = st.file_uploader("Upload Your Resume")

        if st.button("🚀 Analyze My Resume"):
            if not jd_file or not resume_file:
                st.warning("Please upload both files.")
            else:
                jd_content = get_file_text(jd_file)
                resume_content = get_file_text(resume_file)
                with st.spinner("🧠 Gemini is performing a deep analysis..."):
                    analysis_result = analyze_with_gemini(clean_text(resume_content), clean_text(jd_content))
                    if "error" in analysis_result:
                        st.error(analysis_result['error'])
                    else:
                        st.success("Analysis complete!")
                        display_analysis_results(analysis_result, show_feedback=True)

elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect')
elif st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password to continue.')
