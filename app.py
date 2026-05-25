import streamlit as st
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
import re
import io

st.set_page_config(page_title="Enterprise SOP and RCM", layout="wide")
st.title("Enterprise SOP and RCM Analyzer")

# -----------------------------------
# EXTRACT TEXT
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
# CHUNK TEXT
# -----------------------------------
def chunk_text(text):
    parts = re.split(r"\n|\•|-|\.", text)
    return [p.strip() for p in parts if len(p.strip()) > 40]


# -----------------------------------
# CONTROL DETECTION
# -----------------------------------
def is_control_statement(text):
    text = text.lower()

    signals = [
        "shall", "must", "should", "required",
        "needs to", "has to", "ensure",
        "responsible", "obligated",
        "at least", "minimum"
    ]

    return any(s in text for s in signals)


# -----------------------------------
# GENERATE CONTROL (KEY FEATURE)
# -----------------------------------
def generate_control(sop):

    sop_lower = sop.lower()

    owner = "Process owner"
    action = "perform control"
    frequency = ""
    evidence = "and retain evidence"

    # Owner
    if "buyer" in sop_lower:
        owner = "Buyer"
    elif "manager" in sop_lower:
        owner = "Manager"

    # Action
    if "review" in sop_lower:
        action = "review the process"
    elif "communicate" in sop_lower:
        action = "communicate details to vendors"
    elif "invite" in sop_lower:
        action = "invite vendors"
    elif "evaluate" in sop_lower:
        action = "evaluate vendors"
    elif "conduct" in sop_lower:
        action = "conduct auction"

    # Frequency
    if "year" in sop_lower:
        frequency = "annually"
    elif "day" in sop_lower:
        frequency = "at least 1 day before event"
    elif "hour" in sop_lower:
        frequency = "within defined time"
    
    # Threshold rule
    if "at least 3" in sop_lower or "minimum 3" in sop_lower:
        return "Auction shall be conducted only if at least 3 vendors participate."

    return f"{owner} shall {action} {frequency} {evidence}."


# -----------------------------------
# KEYWORD MATCHING
# -----------------------------------
def get_keywords(text):
    words = text.lower().split()
    key_terms = ["vendor", "auction", "price", "bid", "review", "communication"]
    return [w for w in words if w in key_terms]


# -----------------------------------
# MATCH ENGINE
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

    if score == 0:
        issue = "Missing control"
    elif score == 1:
        issue = "Weak control"
    else:
        issue = "Related"

    suggestion = generate_control(sop)

    return best_match, issue, suggestion


# -----------------------------------
# UPLOAD FILES
# -----------------------------------
uploaded_files = st.file_uploader(
    "Upload SOP / RCM / Framework Files",
    type=["pdf", "docx", "xlsx"],
    accept_multiple_files=True
)


# -----------------------------------
# RUN
# -----------------------------------
if st.button("Run Analysis"):

    if uploaded_files:

        sop_texts = []
        rcm_rows = []

        # FILE CLASSIFICATION
        for file in uploaded_files:

            if file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
                rows = df.astype(str).agg(" | ".join, axis=1).tolist()
                rcm_rows.extend(rows)

            else:
                text = extract_text(file)

                if "risk" in text.lower() and "control" in text.lower():
                    rcm_rows.extend(chunk_text(text))
                else:
                    sop_texts.append(text)

        # MERGE SOP
        all_sop = "\n".join(sop_texts)
        sop_chunks = chunk_text(all_sop)

        st.write(f"SOP chunks detected: {len(sop_chunks)}")

        results = []

        # PRIMARY ANALYSIS
        for sop in sop_chunks:

            if not is_control_statement(sop):
                continue

            match, issue, suggestion = compare(sop, rcm_rows)

            results.append({
                "SOP Statement": sop,
                "Best Match": match,
                "Issue": issue,
                "Recommendation": suggestion
            })

        # ✅ FALLBACK LOGIC
        if len(results) == 0:
            st.warning("⚠ No strict controls found — using fallback mode")

            for sop in sop_chunks[:30]:
                match, issue, suggestion = compare(sop, rcm_rows)

                results.append({
                    "SOP Statement": sop,
                    "Best Match": match,
                    "Issue": issue,
                    "Recommendation": suggestion
                })

        df = pd.DataFrame(results)

        # ✅ PRIORITY COLUMN
        df["Priority"] = df["Issue"].apply(
            lambda x: "High" if x == "Missing control"
            else "Medium" if x == "Weak control"
            else "Low"
        )

        st.success(f"Analysis Completed ({len(df)} points)")
        st.dataframe(df)

        # -----------------------------------
        # ✅ EXCEL DOWNLOAD (MULTI-SHEET)
        # -----------------------------------
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="All Results")

            df[df["Issue"]=="Missing control"].to_excel(
                writer, index=False, sheet_name="Missing Controls"
            )

            df[df["Issue"]=="Weak control"].to_excel(
                writer, index=False, sheet_name="Weak Controls"
            )

        excel_data = output.getvalue()

        st.download_button(
            label="Download Excel Report",
            data=excel_data,
            file_name="SOP_RCM_Analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.error("Please upload files first.")
