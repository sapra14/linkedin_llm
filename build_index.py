import pandas as pd
import json
import faiss
import os
from embedder import get_embeddings

STANDARD_COLUMNS = [
    'name', 'profile_url', 'author', 'authorUrl', 'description',
    'postContent', 'postUrl', 'postDate', 'type', 'likeCount',
    'commentCount', 'repostCount', 'followers'
]

def clean_and_standardize(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [col.strip().lower() for col in df.columns]
    rename_map = {
        'profileurl': 'profile_url',
        'authorurl': 'authorUrl',
        'posturl': 'postUrl',
        'postcontent': 'postContent',
        'likecount': 'likeCount',
        'commentcount': 'commentCount',
        'repostcount': 'repostCount',
        'postdate': 'postDate',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ''
    return df[STANDARD_COLUMNS]

def load_and_prepare_profiles(csv_files):
    df_list = []
    for file in csv_files:
        if os.path.exists(file):
            df = pd.read_csv(file, encoding='utf-8')
            df_clean = clean_and_standardize(df)
            print(f"Loaded {file} with columns: {df_clean.columns.tolist()}")
            print(f"Sample postContent:\n{df_clean['postContent'].head()}")
            df_list.append(df_clean)
        else:
            print(f"File not found: {file}")

    combined_df = pd.concat(df_list, ignore_index=True).fillna('')
    combined_df.to_json("raw_metadata.json", orient="records", indent=2)
    print("Saved raw_metadata.json with shape:", combined_df.shape)
    texts = [row_to_text(row) for _, row in combined_df.iterrows()]
    return texts

def row_to_text(row):
    return f"""Name: {row.get('name', '')}
Profile URL: {row.get('profile_url', '')}
Author: {row.get('author', '')}
Author URL: {row.get('authorUrl', '')}
Description: {row.get('description', '')}
Post Content: {row.get('postContent', '')}
Post URL: {row.get('postUrl', '')}
Post Date: {row.get('postDate', '')}
Type: {row.get('type', '')}
Likes: {row.get('likeCount', '')}
Comments: {row.get('commentCount', '')}
Reposts: {row.get('repostCount', '')}
Followers: {row.get('followers', '')}
"""

def build_and_save_index(texts, index_path="linkedin_index.faiss", docs_path="docs.json"):
    embeddings = get_embeddings(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, index_path)
    with open(docs_path, "w") as f:
        json.dump(texts, f, indent=2)
    print(f"Saved FAISS index and docs ({len(texts)} profiles)")

if __name__ == "__main__":
    csv_files = ["data/merged_profiles.csv"]
    texts = load_and_prepare_profiles(csv_files)
    build_and_save_index(texts)
