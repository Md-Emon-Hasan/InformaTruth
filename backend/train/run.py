import data_loader
import trainer
import utils
import sys
import os

# Add parent directory to path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODEL_NAME
from train.config import MODEL_PATH  # Use training config for output path

from transformers import RobertaTokenizer
from transformers import RobertaForSequenceClassification


def main():
    # Load and prepare data
    print("Loading data...")
    dataset = data_loader.load_and_prepare_data(
        train_file="../liar_dataset/train.tsv",
        val_file="../liar_dataset/valid.tsv",
        test_file="../liar_dataset/test.tsv",
    )

    # Initialize tokenizer and tokenize dataset
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
    dataset = utils.tokenize_dataset(dataset, tokenizer)

    # Initialize model
    model = RobertaForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=2, problem_type="single_label_classification"
    )

    # Train model
    trainer.train_model(dataset, model, tokenizer)

    # Save model
    model.save_pretrained(MODEL_PATH)
    tokenizer.save_pretrained(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
