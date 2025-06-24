from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embeddings(text_list):
    embeddings = model.encode(text_list, convert_to_numpy=True).astype('float32')
    return embeddings
