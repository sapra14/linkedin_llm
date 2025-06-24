# vector_store.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json

def build_vector_store():
    with open("linkedin_profiles.json", "r") as f:
        data = json.load(f)

    # Prepare documents as text for embeddings
    documents = [f"{p['name']} - {p['title']}" for p in data]

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, "linkedin_index.faiss")

    with open("docs.json", "w") as f:
        json.dump(documents, f, indent=4)

if __name__ == "__main__":
    build_vector_store()
