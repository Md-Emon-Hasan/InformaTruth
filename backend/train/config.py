MODEL_NAME = "roberta-base"
MODEL_PATH = "./fine_tuned_liar_detector"
DATASET_NAME = "liar"

# Tokenization — must match inference (see backend/config.MAX_LENGTH)
MAX_LENGTH = 256

# --- QLoRA hyper-parameters (mirror notebook/Experiment_QLoRA) ---------------
# 4-bit NF4 base + LoRA adapters on the attention projections.
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
LORA_TARGET_MODULES = ["query", "key", "value"]
