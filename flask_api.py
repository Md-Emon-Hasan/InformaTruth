from flask import Flask, request, jsonify
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AutoTokenizer, AutoModelForSeq2SeqLM
import newspaper
import fitz

# Initialize Flask app
app = Flask(__name__)

# Load the fine-tuned models (assumed saved in ./fine_tuned_liar_detector)
roberta_tokenizer = RobertaTokenizer.from_pretrained("./fine_tuned_liar_detector")
roberta_model = RobertaForSequenceClassification.from_pretrained("./fine_tuned_liar_detector")
flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

# Helper functions
def extract_text(input_type, value):
    """Extract text from URL, PDF, or text input"""
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

def classify_and_explain(text):
    """Classify text and generate explanation"""
    # Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    roberta_model.to(device)
    flan_model.to(device)

    # Classification
    inputs = roberta_tokenizer(text, return_tensors="pt", truncation=True, padding='max_length', max_length=128).to(device)
    with torch.no_grad():
        logits = roberta_model(**inputs).logits
    probs = torch.softmax(logits, dim=1)
    pred = torch.argmax(probs, dim=1).item()
    confidence = probs[0][pred].item()
    label = "Real" if pred == 0 else "Fake"

    # Explanation
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

# API route to handle requests
@app.route('/analyze', methods=['POST'])
def analyze_news():
    data = request.json

    input_type = data.get('input_type')
    value = data.get('value')

    # Extract text
    text = extract_text(input_type, value)
    if text.startswith("Error") or text == "Invalid input type":
        return jsonify({"error": text}), 400

    # Classify and explain
    label, confidence, explanation = classify_and_explain(text)

    # Return response
    return jsonify({
        "label": label,
        "confidence": round(confidence, 2),
        "explanation": explanation
    })

# Root route to avoid 404 errors
@app.route('/')
def home():
    return "Welcome to the Fake News Detection API! Please use the /analyze endpoint to send a POST request."

if __name__ == "__main__":
    app.run(debug=True)
