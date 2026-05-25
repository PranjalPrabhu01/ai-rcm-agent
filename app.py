import streamlit as st
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
import re

st.set_page_config(page_title="Enterprise SOP vs RCM", layout="wide")
st.title("🧠 Enterprise SOP vs RCM Analyzer (No AI Required)")

# -----------------------------------
# EXTRACT TEXT FROM FILES
# -----------------------------------
def extract_text(file):
    text = ""

    if file.name.endswith(".docx"):
        doc = Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])

    elif file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    return text

# -----------------------------------
# CHUNK TEXT INTO STATEMENTS
# -----------------------------------
def chunk_text(text):
    parts = re.split(r"\n|\•|-", text)
    return [p.strip() for p in parts if len(p.strip()) > 40]

# -----------------------------------
# IDENTIFY CONTROL STATEMENTS
# -----------------------------------
def is_control_statement(text):
    keywords = ["shall", "must", "should", "required", "at least", "minimum"]
    return any(k in text.lower() for k in keywords)

# -----------------------------------
# GENERATE CONTROL SUGGESTION
# -----------------------------------
def generate_control(sop):

    sop_lower = sop.lower()

    owner = "Process owner"
    action = "perform control"
    frequency = ""
    evidence = "and retain evidence"

    # detect owner
    if "buyer" in sop_lower:
        owner = "Buyer"
    elif "manager" in sop_lower:
        owner = "Manager"

    # detect action
    if "review" in sop_lower:
        action = "review the process"
    elif "communicate" in sop_lower:
        action = "communicate details to vendors"
    elif "invite" in sop_lower:
        action = "invite vendors"
    elif "evaluate" in sop_lower:
        action = "evaluate vendor proposals"
    elif "conduct" in sop_lower:
        action = "conduct auction"
    elif "approve" in sop_lower:
        action = "approve transactions"

    # detect frequency
    if "year" in sop_lower:
        frequency = "annually"
    elif "day" in sop_lower:
        frequency = "at least 1 day before event"
    elif "weekly" in sop_lower:
        frequency = "weekly"

    # detect threshold
    if "at least 3" in sop_lower or "minimum 3" in sop_lower:
        return "Auction shall be conducted only if at least 3 vendors participate."

    return f"{owner} shall {action} {frequency} {evidence}."

# -----------------------------------
# KEYWORD MATCHING
# -----------------------------------
def get_keywords(text):
    words = text.lower().split()
    important = ["vendor", "auction", "price", "bid", "review", "approve", "communication"]
    return [w for w in words if w in important]

# -----------------------------------
# COMPARE SOP VS RCM
# -----------------------------------
def compare(sop, rcm_rows):

    sop_keys = get_keywords(sop)

    best_match = ""
    score = 0

    for row in rcm_rows:
        row_lower = row.lower()
        match_score = sum(k in row_lower for k in sop_keys)

        if match_score > score:
            score = match_score
            best_match = row

    # issue classification
    if score == 0:
        issue = "Missing control"
    elif score == 1:
        issue = "Weak control"
    else:
        issue = "Related"

    suggestion = generate_control(sop)

    return best_match, issue, suggestion

# -----------------------------------
# FILE UPLOAD (MULTIPLE)
# -----------------------------------
uploaded_files = st.file_uploader(
    "Upload Files (SOP, RCM, Framework - Multiple Allowed)",
    type=["pdf", "docx", "xlsx"],
    accept_multiple_files=True
)

# -----------------------------------
# RUN ANALYSIS
# -----------------------------------
if st.button("Run Analysis"):

    if uploaded_files:

        sop_texts = []
        rcm_rows = []

        # classify files
        for file in uploaded_files:

            if file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
                rows = df.astype(str).agg(" | ".join, axis=1).tolist()
                rcm_rows.extend(rows)

            else:
                text = extract_text(file)

                if "risk" in text.lower() and "control" in text.lower():
                    # treat as RCM-like doc
                    chunks = chunk_text(text)
                    rcm_rows.extend(chunks)
                else:
                    sop_texts.append(text)

        # merge SOPs
        all_sop = "\n".join(sop_texts)
        sop_chunks = chunk_text(all_sop)

        results = []

        for sop in sop_chunks:

            # skip non-controls
            if not is_control_statement(sop):
                continue

            match, issue, suggestion = compare(sop, rcm_rows)

            results.append({
                "SOP Statement": sop,
                "Best Match in RCM": match,
                "Issue": issue,
                "Exact Recommendation": suggestion
            })

        df = pd.DataFrame(results)

        st.success(f"✅ Analysis Completed ({len(df)} control points found)")
        st.dataframe(df)

        # download
        df.to_excel("final_rcm_output.xlsx", index=False)

        with open("final_rcm_output.xlsx", "rb") as f:
            st.download_button("📥 Download Report", f)

    else:
        st.error("Please upload at least one file.")
