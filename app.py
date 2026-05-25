import streamlit as st
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
import re

st.title("📊 SOP and RCM Analyzer")

# ---------------------
# Extract text
# ---------------------
def extract_text(file):
    if file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        reader = PdfReader(file)
        return "".join([p.extract_text() or "" for p in reader.pages])

# ---------------------
# Chunk SOP
# ---------------------
def chunk_text(text):
    parts = re.split(r"\n|\•|-", text)
    return [p.strip() for p in parts if len(p.strip()) > 40]

# ---------------------
# Detect keywords
# ---------------------
def detect_keywords(text):
    keywords = []
    
    if "vendor" in text.lower():
        keywords.append("vendor")
    if "auction" in text.lower():
        keywords.append("auction")
    if "price" in text.lower():
        keywords.append("price")
    if "minimum" in text.lower() or "at least" in text.lower():
        keywords.append("threshold")
    
    return keywords

# ---------------------
# Compare logic
# ---------------------
def compare(sop, rcm_rows):

    sop_keys = detect_keywords(sop)

    best_match = ""
    match_score = 0

    for row in rcm_rows:
        score = sum(k in row.lower() for k in sop_keys)

        if score > match_score:
            match_score = score
            best_match = row

    # Rules
    if match_score == 0:
        issue = "Missing control"
        suggestion = "Add control based on SOP"
    
    elif match_score < 2:
        issue = "Weak match"
        suggestion = "Improve wording and coverage"
    
    else:
        issue = "Related"
        suggestion = "OK or improve clarity"

    return best_match, issue, suggestion

# ---------------------
# UI
# ---------------------
sop_file = st.file_uploader("Upload SOP", type=["pdf", "docx"])
rcm_file = st.file_uploader("Upload RCM", type=["xlsx"])

if st.button("Run Analysis"):

    if sop_file and rcm_file:

        sop_text = extract_text(sop_file)
        sop_chunks = chunk_text(sop_text)

        rcm_df = pd.read_excel(rcm_file)
        rcm_rows = rcm_df.astype(str).agg(" | ".join, axis=1).tolist()

        results = []

        for sop in sop_chunks:

            match, issue, suggestion = compare(sop, rcm_rows)

            results.append({
                "SOP": sop,
                "Best Match": match,
                "Issue": issue,
                "Suggestion": suggestion
            })

        df = pd.DataFrame(results)

        st.success("✅ Analysis Complete")
        st.dataframe(df)

        df.to_excel("output.xlsx", index=False)

        with open("output.xlsx", "rb") as f:
            st.download_button("Download Report", f)

    else:
        st.error("Upload both files")
