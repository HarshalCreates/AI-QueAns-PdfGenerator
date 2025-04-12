import streamlit as st
from pathlib import Path
import fitz  # PyMuPDF
from groq import Groq
from fpdf import FPDF

# Initialize Groq client


client = Groq(api_key=st.secrets["GROQ_API_KEY"])
# ---------- Function Definitions ---------- #

def extract_questions_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    questions = []
    question_starters = (
        "what", "explain", "define", "list", "how", "why", "write", 
        "describe", "identify", "differentiate", "state", "give", "mention"
    )
    for page in doc:
        text = page.get_text()
        for line in text.split('\n'):
            clean_line = line.strip().lower()
            for starter in question_starters:
                if starter in clean_line[:len(starter)+3]:  # e.g., "1. define", "Q2: explain"
                    questions.append(line.strip())
                    break
    return questions

def generate_answer(question):
    prompt = f"Answer the following question clearly and concisely:\n\n{question}"
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating answer: {e}"

def create_pdf(questions, answers, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for idx, (q, a) in enumerate(zip(questions, answers)):
        pdf.multi_cell(0, 10, f"Q{idx+1}: {q}\nA{idx+1}: {a}\n\n", border=0)
    pdf.output(output_path)

# ---------- Streamlit UI ---------- #

st.set_page_config(page_title="AI PDF Q&A Generator", layout="centered", page_icon="📄")

# Sidebar Info
with st.sidebar:
    st.title("🧠 PDF Q&A AI")
    st.markdown("""
        This tool allows you to:
        - Upload a PDF with academic-style questions
        - Automatically extract and answer questions using AI
        - Download a professionally formatted Answer Sheet

        **Powered by Groq + LLaMA3**
    """)
    

# Main Section
st.title("📄 AI-Powered PDF Question Answering")
st.markdown("Upload a question-based PDF and generate intelligent answers instantly.")

# File Upload
uploaded_file = st.file_uploader("📎 Upload Your PDF File", type="pdf")

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    if st.button("🚀 Generate Answers"):
        with st.spinner("Processing your PDF... This might take a few moments."):
            questions = extract_questions_from_pdf(uploaded_file)

            if not questions:
                st.warning("No questions found in the uploaded PDF.")
            else:
                answers = [generate_answer(q) for q in questions]
                output_path = "AnswerSheet.pdf"
                create_pdf(questions, answers, output_path)

                st.success("🎉 Answer Sheet is ready!")

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Your Answer Sheet",
                        data=f,
                        file_name="AnswerSheet.pdf",
                        mime="application/pdf"
                    )

        st.markdown("---")
        st.markdown("🔍 **Preview of Extracted Questions**")
        for i, q in enumerate(questions, start=1):
            st.markdown(f"**Q{i}:** {q}")

else:
    st.info("Please upload a PDF file to get started.")
