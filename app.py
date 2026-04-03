import streamlit as st
import pandas as pd
from utils import extract_pdf, extract_docx
import spacy
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Resume Analyzer PRO", layout="wide")

st.title("🚀 AI Resume Analyzer PRO")

# -----------------------------
# LOAD NLP
# -----------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except:
    st.error("Run: python -m spacy download en_core_web_sm")
    st.stop()

# -----------------------------
# INPUT
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📄 Upload Resume", type=["pdf", "docx"])

with col2:
    job_desc = st.text_area("💼 Paste Job Description")

if uploaded_file is None:
    st.warning("⚠ Upload resume to continue")
    st.stop()

# -----------------------------
# EXTRACT TEXT
# -----------------------------
if uploaded_file.type == "application/pdf":
    resume_text = extract_pdf(uploaded_file)
else:
    resume_text = extract_docx(uploaded_file)

if not resume_text.strip():
    st.error("❌ Could not read resume")
    st.stop()

# -----------------------------
# PREVIEW
# -----------------------------
with st.expander("📄 Resume Preview"):
    st.write(resume_text[:1500])

# -----------------------------
# LOAD SKILLS (UPDATED FORMAT)
# -----------------------------
skills_df = pd.read_csv("skills.csv")

if "skill" in skills_df.columns:
    skills_list = skills_df["skill"].tolist()
else:
    skills_list = skills_df["skills"].tolist()

# -----------------------------
# SKILL DETECTION
# -----------------------------
found_skills = [s for s in skills_list if s.lower() in resume_text.lower()]

st.subheader("🧠 Skills Analysis")

col1, col2 = st.columns(2)

with col1:
    st.success(f"Found Skills ({len(found_skills)})")
    st.write(found_skills if found_skills else "None")

with col2:
    st.info(f"Total Skills in Dataset: {len(skills_list)}")

# -----------------------------
# KPI DASHBOARD
# -----------------------------
word_count = len(resume_text.split())

k1, k2, k3 = st.columns(3)

k1.metric("📄 Words", word_count)
k2.metric("🧠 Skills Found", len(found_skills))
k3.metric("📚 Total Skills", len(skills_list))

# -----------------------------
# ATS SCORE
# -----------------------------
skills_score = len(found_skills) / len(skills_list)
length_score = 1 if 300 <= word_count <= 800 else 0.5

ats_score = (skills_score * 0.6 + length_score * 0.4) * 100

st.subheader("📊 ATS Score")
st.metric("ATS Score", f"{ats_score:.2f}%")
st.progress(int(ats_score))

# -----------------------------
# JOB MATCH
# -----------------------------
if job_desc.strip() == "":
    st.warning("👉 Add Job Description for advanced analysis")
    st.stop()

resume_doc = nlp(resume_text)
job_doc = nlp(job_desc)

similarity = resume_doc.similarity(job_doc)

st.subheader("🎯 Job Match Analysis")

col1, col2 = st.columns(2)

with col1:
    st.metric("Match Score", f"{similarity*100:.2f}%")
    st.progress(int(similarity * 100))

with col2:
    if similarity > 0.75:
        st.success("Excellent Match ✅")
    elif similarity > 0.5:
        st.warning("Average Match ⚠")
    else:
        st.error("Low Match ❌")

# -----------------------------
# CATEGORY DASHBOARD (NEW)
# -----------------------------
if "category" in skills_df.columns:

    st.subheader("📊 Skill Category Dashboard")

    category_results = []

    for category in skills_df["category"].unique():
        category_skills = skills_df[skills_df["category"] == category]["skill"].tolist()

        found = [s for s in category_skills if s in found_skills]

        match_percent = (len(found) / len(category_skills)) * 100 if category_skills else 0

        category_results.append({
            "Category": category,
            "Match %": round(match_percent, 2)
        })

    category_df = pd.DataFrame(category_results)

    st.dataframe(category_df, use_container_width=True)

    # BAR CHART
    st.subheader("📈 Category Match Chart")
    st.bar_chart(category_df.set_index("Category")["Match %"])



# -----------------------------
# MISSING SKILLS
# -----------------------------
job_skills = [s for s in skills_list if s.lower() in job_desc.lower()]
missing_skills = list(set(job_skills) - set(found_skills))

st.subheader("⚠ Skill Gap Analysis")

if missing_skills:
    st.warning(missing_skills[:10])
else:
    st.success("No missing skills 🎉")

# -----------------------------
# FEEDBACK
# -----------------------------
st.subheader("🤖 Smart Feedback")

feedback_points = []

if similarity > 0.75:
    feedback_points.append("✔ Strong alignment with job requirements.")
elif similarity > 0.5:
    feedback_points.append("⚠ Moderate alignment. Improve keywords.")
else:
    feedback_points.append("❌ Low match. Major improvements needed.")

if missing_skills:
    feedback_points.append(f"📌 Add skills: {', '.join(missing_skills[:5])}")

if word_count < 300:
    feedback_points.append("📄 Resume too short.")
elif word_count > 800:
    feedback_points.append("📄 Resume too long.")

feedback_points.append("🚀 Use action verbs & measurable achievements.")

for point in feedback_points:
    st.write(point)

# -----------------------------
# PDF DOWNLOAD
# -----------------------------
st.subheader("📄 Export Report")

if st.button("Download PDF Report"):

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(temp_file.name)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("AI Resume Analyzer Report", styles['Title']),
        Paragraph(f"ATS Score: {ats_score:.2f}%", styles['Normal']),
        Paragraph(f"Match Score: {similarity*100:.2f}%", styles['Normal']),
        Paragraph(f"Skills Found: {', '.join(found_skills)}", styles['Normal']),
        Paragraph("Feedback:", styles['Heading2'])
    ]

    for point in feedback_points:
        content.append(Paragraph(point, styles['Normal']))

    doc.build(content)

    with open(temp_file.name, "rb") as f:
        st.download_button("⬇ Download Report", f, file_name="resume_report.pdf")