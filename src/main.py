from transformers import RobertaTokenizer
from data import load_and_prepare_data, tokenize_dataset
from model import load_model, train_model
from inference import load_flan, classify_and_explain
from config import SAVED_MODEL_DIR
import os
from logger import setup_logger

log = setup_logger("Main")

# Load and preprocess data
dataset = load_and_prepare_data()
tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
dataset = tokenize_dataset(dataset, tokenizer)

# Load and fine-tune model
model = load_model()
trainer = train_model(model, dataset)

# Save model
os.makedirs(SAVED_MODEL_DIR, exist_ok=True)
model.save_pretrained(SAVED_MODEL_DIR)
tokenizer.save_pretrained(SAVED_MODEL_DIR)
log.info("Model saved to disk.")

# Inference Example
flan_tokenizer, flan_model = load_flan()
example_text = "The moon landing was staged in a Hollywood studio."
label, confidence, explanation = classify_and_explain(example_text, model, tokenizer, flan_model, flan_tokenizer)

log.info("\n🔍 Prediction Results:")
log.info(f"🏷️ Label: {label}")
log.info(f"📊 Confidence: {confidence:.2f}")
log.info(f"💡 Explanation: {explanation}")