import streamlit as st
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
import re
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI SOP vs RCM", layout="wide")
st.title("🧠 SOP vs RCM AI Agent")

# ---------------------
# Extract text
# ---------------------
def extract_text(file):
    if file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

# ---------------------
# Chunk SOP
# ---------------------
def chunk_text(text):
    chunks = re.split(r"\n|\•|-", text)
    return [c.strip() for c in chunks if len(c.strip()) > 40]

# ---------------------
# UI
# ---------------------
sop_file = st.file_uploader("Upload SOP (PDF/DOCX)", type=["pdf", "docx"])
rcm_file = st.file_uploader("Upload RCM Excel", type=["xlsx"])

if st.button("Run Analysis"):

    if sop_file and rcm_file:

        sop_text = extract_text(sop_file)
        sop_chunks = chunk_text(sop_text)

        rcm_df = pd.read_excel(rcm_file)
        rcm_rows = rcm_df.astype(str).agg(" | ".join, axis=1).tolist()

        results = []

        for sop in sop_chunks[:30]:  # limit for cost control

            prompt = f"""
You are an audit expert.

SOP:
{sop}

RCM:
{rcm_rows[:5]}

Return:
- Relationship: Related / Not related
- Missing points
- Incorrect points
- Suggested edits
- Justification (quote SOP)

Output JSON.
"""

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )

                output = response.choices[0].message.content

            except Exception as e:
                output = str(e)

            results.append({
                "SOP": sop,
                "AI Analysis": output
            })

        df = pd.DataFrame(results)

        st.success("✅ Done")
        st.dataframe(df)

        df.to_excel("output.xlsx", index=False)

        with open("output.xlsx", "rb") as f:
            st.download_button("Download Report", f)

    else:
        st.error("Upload both files")
