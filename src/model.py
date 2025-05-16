# 🧠 model.py — Model Loading & Training
# ========================================
from transformers import RobertaForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch
from config import *
from logger import setup_logger

log = setup_logger("Model")

def load_model():
    log.info("Loading RobertaForSequenceClassification model...")
    model = RobertaForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        problem_type="single_label_classification"
    )
    return model

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def train_model(model, dataset):
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=TRAIN_EPOCHS,
        weight_decay=0.01,
        logging_steps=50,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy"
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset['train'],
        eval_dataset=dataset['validation'],
        compute_metrics=compute_metrics
    )
    log.info("Training started...")
    trainer.train()
    log.info("Training complete.")
    return trainer