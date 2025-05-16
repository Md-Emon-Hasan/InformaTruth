# ========================================
# 📦 data.py — Data Loading & Preprocessing
# ========================================
import pandas as pd
from datasets import load_dataset, Dataset
from config import MAX_SEQ_LENGTH
from transformers import RobertaTokenizer
from logger import setup_logger

log = setup_logger("DataLoader")

def load_and_prepare_data():
    dataset = load_dataset("liar")
    log.info("Dataset loaded from 'liar'.")

    def map_labels(label):
        return 0 if label in [4, 5] else 1

    def clean(df):
        df['label'] = df['label'].apply(map_labels).astype(int)
        cleaned = df.dropna(subset=['label', 'statement'])
        log.info(f"Cleaned dataset shape: {cleaned.shape}")
        return cleaned

    df_train = clean(pd.DataFrame(dataset['train']))
    df_val = clean(pd.DataFrame(dataset['validation']))
    df_test = clean(pd.DataFrame(dataset['test']))

    return {\        'train': Dataset.from_pandas(df_train),
        'validation': Dataset.from_pandas(df_val),
        'test': Dataset.from_pandas(df_test)
    }

def tokenize_dataset(dataset, tokenizer):
    def tokenize(batch):
        return tokenizer(batch['statement'], truncation=True, padding='max_length', max_length=MAX_SEQ_LENGTH)

    for split in dataset:
        dataset[split] = dataset[split].map(tokenize, batched=True)
        dataset[split].set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
        log.info(f"Tokenized '{split}' dataset with {len(dataset[split])} samples.")
    return dataset