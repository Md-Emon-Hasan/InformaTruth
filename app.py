# Import necessary libraries
import streamlit as st
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import newspaper
import fitz
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import os

# ========================================
# 🏗️ Setup & Initialization
# ========================================
# Dynamically resolve the path to the fine-tuned RoBERTa model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Current file directory
MODEL_DIR = os.path.join(BASE_DIR, "fine_tuned_liar_detector")  # Adjust as needed

# Load Fine-Tuned RoBERTa
roberta_tokenizer = RobertaTokenizer.from_pretrained(MODEL_DIR)
model = RobertaForSequenceClassification.from_pretrained(MODEL_DIR)

# Initialize FLAN-T5 for Explanation
flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

# Function to extract text from different input types
def extract_text(input_type, value):
    try:
        if input_type == 'url':
            article = newspaper.Article(value)
            article.download()
            article.parse()
            return article.text
        elif input_type == 'pdf':
            with fitz.open(value) as doc:
                return "\n".join([page.get_text() for page in doc])
        elif input_type == 'text':
            return value
        else:
            return "Invalid input type"
    except Exception as e:
        return f"Error processing input: {str(e)}"

# Function to classify and explain the news
def classify_and_explain(text):
    """Classify text and generate explanation"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    flan_model.to(device)
    
    # Classification with fine-tuned RoBERTa
    inputs = roberta_tokenizer(text, return_tensors="pt", truncation=True, padding='max_length', max_length=128).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=1)
    pred = torch.argmax(probs, dim=1).item()
    confidence = probs[0][pred].item()
    label = "Real" if pred == 0 else "Fake"

    # Explanation with FLAN-T5
    prompt = f"Explain why this news might be {label.lower()} in one sentence: {text}"
    explanation_inputs = flan_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
    explanation_ids = flan_model.generate(
        explanation_inputs['input_ids'],
        max_new_tokens=100,
        num_beams=5,
        early_stopping=True
    )
    explanation = flan_tokenizer.decode(explanation_ids[0], skip_special_tokens=True)
    
    return label, confidence, explanation

# ========================================
# 🧪 Streamlit Web App UI
# ========================================
def app():
    # Title
    st.title("InformaTruth: AI-Driven News Veracity Analyzer")
    st.markdown("This app uses a fine-tuned RoBERTa model to detect fake news and provides an explanation using FLAN-T5.")
    st.markdown("Developed by Emon Hasan")

    # Input Selection
    input_type = st.selectbox("Select input type:", ['Text', 'URL', 'PDF'])
    
    # Based on the selection, show the corresponding input field
    if input_type == 'Text':
        text_input = st.text_area("Enter News Text:")
        if st.button("Analyze"):
            if text_input:
                label, confidence, explanation = classify_and_explain(text_input)
                st.write(f"🏷️ **Label**: {label}")
                st.write(f"📊 **Confidence**: {confidence:.2f}")
                st.write(f"💡 **Explanation**: {explanation}")
            else:
                st.error("Please enter some text to analyze.")
    
    elif input_type == 'URL':
        url_input = st.text_input("Enter News URL:")
        if st.button("Analyze"):
            if url_input:
                text = extract_text(input_type='url', value=url_input)
                label, confidence, explanation = classify_and_explain(text)
                st.write(f"🏷️ **Label**: {label}")
                st.write(f"📊 **Confidence**: {confidence:.2f}")
                st.write(f"💡 **Explanation**: {explanation}")
            else:
                st.error("Please enter a URL to analyze.")
    
    elif input_type == 'PDF':
        pdf_file = st.file_uploader("Upload PDF File:", type="pdf")
        if st.button("Analyze") and pdf_file is not None:
            text = extract_text(input_type='pdf', value=pdf_file)
            label, confidence, explanation = classify_and_explain(text)
            st.write(f"🏷️ **Label**: {label}")
            st.write(f"📊 **Confidence**: {confidence:.2f}")
            st.write(f"💡 **Explanation**: {explanation}")
        else:
            st.error("Please upload a PDF to analyze.")

    st.markdown("---")        
    st.markdown(
        """
        - [![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/md-emon-hasan-695483237/)
        - [![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/8801834363533)
        """
    )
            
# Run the Streamlit app
if __name__ == "__main__":
    app()