import torch
from transformers import (
    Trainer,
    TrainingArguments,
    AutoModelForSequenceClassification,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_recall_fscore_support

from train.config import (
    MODEL_NAME,
    LORA_R,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_TARGET_MODULES,
)


def compute_metrics(pred):
    """Compute evaluation metrics"""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary"
    )
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}


def build_qlora_model(num_labels=2):
    """Build a QLoRA model: 4-bit NF4 base + LoRA adapters.

    Mirrors notebook/Experiment_QLoRA:
      - 4-bit NF4 base with double quant and bfloat16 compute dtype
      - classifier head kept full-precision (llm_int8_skip_modules)
      - device_map={"": 0} and gradient checkpointing OFF to avoid the
        bitsandbytes 4-bit quant-state AssertionError on small models
      - LoRA on the query/key/value projections (SEQ_CLS task)

    Requires a CUDA GPU (bitsandbytes 4-bit kernels are GPU-only).
    """
    if not torch.cuda.is_available():
        raise RuntimeError(
            "QLoRA training requires a CUDA GPU (bitsandbytes 4-bit kernels). "
            "Run training on a GPU host, e.g. the Colab notebook."
        )

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        llm_int8_skip_modules=["classifier"],
    )

    base_model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        quantization_config=bnb_config,
        device_map={"": 0},
    )

    base_model = prepare_model_for_kbit_training(
        base_model, use_gradient_checkpointing=False
    )

    peft_config = LoraConfig(
        task_type="SEQ_CLS",
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        target_modules=LORA_TARGET_MODULES,
    )

    model = get_peft_model(base_model, peft_config)
    model.print_trainable_parameters()
    return model


def train_model(dataset, model, tokenizer):
    """Train the model (QLoRA: only the LoRA adapter + head are updated)."""
    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        # QLoRA uses a higher LR than full fine-tuning since only the
        # low-rank adapters are trained.
        learning_rate=2e-4,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=5,
        weight_decay=0.01,
        logging_steps=50,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        bf16=torch.cuda.is_available(),
        # Keep gradient checkpointing OFF: it triggers a bitsandbytes 4-bit
        # quant-state AssertionError on small models like roberta-base.
        gradient_checkpointing=False,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()
    return trainer
