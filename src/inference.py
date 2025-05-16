# ========================================
# 📈 inference.py — Inference Pipeline
# ========================================
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from logger import setup_logger
import torch
from config import FLAN_MODEL_NAME, MAX_SEQ_LENGTH

log = setup_logger("Inference")

def load_flan():
    tokenizer = AutoTokenizer.from_pretrained(FLAN_MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(FLAN_MODEL_NAME)
    log.info("FLAN-T5 model and tokenizer loaded.")
    return tokenizer, model

def classify_and_explain(text, clf_model, clf_tokenizer, flan_model, flan_tokenizer):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clf_model.to(device)
    flan_model.to(device)

    inputs = clf_tokenizer(text, return_tensors="pt", truncation=True, padding='max_length', max_length=MAX_SEQ_LENGTH).to(device)
    with torch.no_grad():
        logits = clf_model(**inputs).logits
    probs = torch.softmax(logits, dim=1)
    pred = torch.argmax(probs, dim=1).item()
    confidence = probs[0][pred].item()
    label = "Real" if pred == 0 else "Fake"
    log.info(f"Prediction: {label}, Confidence: {confidence:.2f}")

    prompt = f"Explain why this news might be {label.lower()} in one sentence: {text}"
    expl_inputs = flan_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
    expl_ids = flan_model.generate(expl_inputs['input_ids'], max_new_tokens=100, num_beams=5, early_stopping=True)
    explanation = flan_tokenizer.decode(expl_ids[0], skip_special_tokens=True)
    log.info(f"Explanation generated: {explanation}")

    return label, confidence, explanation