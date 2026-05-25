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
