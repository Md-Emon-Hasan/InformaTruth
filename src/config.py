# ========================================
# 🔧 config.py — Configuration Settings
# ========================================
MODEL_NAME = "roberta-base"
FLAN_MODEL_NAME = "google/flan-t5-base"
MAX_SEQ_LENGTH = 128
TRAIN_EPOCHS = 2
BATCH_SIZE = 16
LEARNING_RATE = 2e-5

# Paths
OUTPUT_DIR = "./results"
SAVED_MODEL_DIR = "./fine_tuned_liar_detector"
LOG_FILE_PATH = "./logs/app.log"