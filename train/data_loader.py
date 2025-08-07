from datasets import load_dataset, Dataset
import pandas as pd

def load_and_prepare_data():
    """Load and preprocess the LIAR dataset"""
    dataset = load_dataset("liar")

    # Convert to DataFrames
    df_train = pd.DataFrame(dataset['train'])
    df_val = pd.DataFrame(dataset['validation'])
    df_test = pd.DataFrame(dataset['test'])

    # Define robust label mapping
    def map_labels(label):
        if isinstance(label, str):
            label = int(label)
        # Map to binary: 0 = real (4,5), 1 = fake (0,1,2,3)
        return 0 if label in [4, 5] else 1

    # Apply label mapping and convert to integers
    for df in [df_train, df_val, df_test]:
        df['label'] = df['label'].apply(map_labels).astype(int)
        df = df.dropna(subset=['label', 'statement'])  # Remove any NA values

    return {
        'train': Dataset.from_pandas(df_train),
        'validation': Dataset.from_pandas(df_val),
        'test': Dataset.from_pandas(df_test)
    }