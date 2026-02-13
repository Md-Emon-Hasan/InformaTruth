def tokenize_dataset(dataset, tokenizer):
    """Tokenize the dataset"""

    def tokenize(batch):
        return tokenizer(
            batch["statement"], truncation=True, padding="max_length", max_length=128
        )

    for split in dataset:
        dataset[split] = dataset[split].map(tokenize, batched=True)
        dataset[split].set_format(
            type="torch", columns=["input_ids", "attention_mask", "label"]
        )
    return dataset
