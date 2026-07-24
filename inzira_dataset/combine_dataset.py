import pandas as pd
import json
import os

print("Loading opportunity pages...")
df_opportunity = pd.read_csv("raw_pages/opportunity_pages.csv")
print(f"Opportunity pages: {len(df_opportunity)}")

print("Loading non-opportunity pages...")
with open("raw_pages/non_opportunity_pages.json", "r", encoding="utf-8") as f:
    non_opp_data = json.load(f)
df_non_opportunity = pd.DataFrame(non_opp_data)
print(f"Non-opportunity pages: {len(df_non_opportunity)}")

# Combine both datasets
df_combined = pd.concat([df_opportunity, df_non_opportunity], ignore_index=True)

# Shuffle the data
df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\nTotal combined dataset: {len(df_combined)} pages")

# Save combined dataset
os.makedirs("labeled_data", exist_ok=True)
df_combined.to_json(
    "labeled_data/full_dataset.json",
    orient="records",
    force_ascii=False,
    indent=2
)

print("✓ Saved to labeled_data/full_dataset.json")

print("\n── DATASET SUMMARY ────────────────────────────────")
print(f"Total pages        : {len(df_combined)}")
print(f"Opportunity pages  : {len(df_opportunity)}")
print(f"Non-opportunity    : {len(df_non_opportunity)}")
print(f"\nBERT labels:")
print(df_combined["bert_label"].value_counts().to_string())
print(f"\nRoBERTa categories:")
print(df_combined["roberta_label"].value_counts().to_string())