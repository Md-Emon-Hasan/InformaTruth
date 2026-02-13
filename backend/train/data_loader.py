from datasets import Dataset
import pandas as pd


def load_and_prepare_data(train_file, val_file, test_file):
    """
    Load LIAR dataset from local TSV files and prepare it for binary classification.

    Binary mapping:
        0 = real (mostly-true, true)
        1 = fake (pants-fire, false, barely-true, half-true)
    """
    # Load TSVs without header
    df_train = pd.read_csv(train_file, sep="\t", header=None)
    df_val = pd.read_csv(val_file, sep="\t", header=None)
    df_test = pd.read_csv(test_file, sep="\t", header=None)

    # Assign proper column names (LIAR structure)
    columns = [
        "id",  # 0
        "label_text",  # 1
        "statement",  # 2
        "subject",  # 3
        "speaker",  # 4
        "job_title",  # 5
        "state_info",  # 6
        "party_affiliation",  # 7
        "barely_true_count",  # 8
        "false_count",  # 9
        "half_true_count",  # 10
        "mostly_true_count",  # 11
        "pants_fire_count",  # 12
        "source",  # 13
    ]

    df_train.columns = columns
    df_val.columns = columns
    df_test.columns = columns

    # Binary label mapping
    def map_labels(label_text):
        fake_labels = ["pants-fire", "false", "barely-true", "half-true"]
        # real_labels = ["mostly-true", "true"] # Unused
        return 1 if label_text in fake_labels else 0

    for df in [df_train, df_val, df_test]:
        df["label"] = df["label_text"].apply(map_labels)
        df.dropna(subset=["label", "statement"], inplace=True)

    # Keep only statement + label for dataset
    hf_dataset = {
        "train": Dataset.from_pandas(df_train[["statement", "label"]]),
        "validation": Dataset.from_pandas(df_val[["statement", "label"]]),
        "test": Dataset.from_pandas(df_test[["statement", "label"]]),
    }

    return hf_dataset
