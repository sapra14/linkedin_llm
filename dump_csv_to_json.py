import pandas as pd
import json

csv_path = "data/merged_profiles.csv"  # your actual path

def dump_csv_to_json(csv_path, json_path="raw_metadata_diagnostic.json"):
    df = pd.read_csv(csv_path, encoding='utf-8')
    print("CSV columns detected:", df.columns.tolist())
    print("CSV rows count:", len(df))
    df = df.fillna('')  # Fill NaNs with empty string to avoid missing data
    df.to_json(json_path, orient="records", indent=2)
    print(f"Dumped CSV to JSON: {json_path}")

if __name__ == "__main__":
    dump_csv_to_json(csv_path)
