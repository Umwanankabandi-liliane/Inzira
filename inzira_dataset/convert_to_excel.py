import pandas as pd
import json

# Load the JSON file
with open("labeled_data/full_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert to dataframe
df = pd.DataFrame(data)

# Save as Excel
df.to_excel("labeled_data/full_dataset.xlsx", index=False)
print(f"Done — {len(df)} pages saved to labeled_data/full_dataset.xlsx")