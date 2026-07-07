import sys
from io import BytesIO
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.resume_matcher import extract_keywords, score_resume


def read_uploaded_file(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    data = uploaded_file.read()
    if suffix == ".txt":
        return data.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    st.error(f"Unsupported file type: {uploaded_file.name}")
    return ""


st.set_page_config(page_title="Resume Matcher", layout="wide")
st.title("Resume Matcher")
st.write("Upload a job description and one or more resumes to see keyword match scores.")

jd_file = st.file_uploader("Job Description", type=["txt", "pdf"])
resume_files = st.file_uploader(
    "Resumes", type=["txt", "pdf"], accept_multiple_files=True
)

if st.button("Score Resumes"):
    if not jd_file:
        st.warning("Please upload a job description.")
    elif not resume_files:
        st.warning("Please upload at least one resume.")
    else:
        jd_text = read_uploaded_file(jd_file)
        jd_keywords = extract_keywords(jd_text)

        if not jd_keywords:
            st.error("No keywords could be extracted from the job description.")
        else:
            results = []
            for f in resume_files:
                text = read_uploaded_file(f)
                score, matched, missing = score_resume(jd_keywords, text)
                results.append((f.name, score, matched, missing))

            results.sort(key=lambda r: r[1], reverse=True)

            st.subheader("Ranked Results")
            st.dataframe(
                [
                    {"Resume": name, "Score (%)": round(score, 1)}
                    for name, score, _, _ in results
                ],
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Details")
            for name, score, matched, missing in results:
                with st.expander(f"{name} — {score:.1f}%"):
                    st.write(f"**Matched ({len(matched)}):** {', '.join(sorted(matched)) or '—'}")
                    st.write(f"**Missing ({len(missing)}):** {', '.join(sorted(missing)) or '—'}")
