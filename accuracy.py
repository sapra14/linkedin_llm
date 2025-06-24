# evaluate_llama_rag_with_faiss.py

from llama_cpp import Llama
from sentence_transformers import SentenceTransformer, util
from collections import Counter
import re
import json
import os
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

# -----------------------------
# 1. Load LLaMA GGUF Model
# -----------------------------
llm = Llama(
    model_path="models/llama-7b.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

# -----------------------------
# 2. Load Corpus + Embed
# -----------------------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Dummy corpus — Replace with real LinkedIn post data
corpus = [
    "Author: Madhuri Jain\npostUrl: https://linkedin.com/in/mjmadhu\nlikeCount: 940\npostContent: Looking for a lawyer in Bangalore.",
    "Author: Ashish Shah\npostUrl: https://linkedin.com/feed/update/urn:li:activity:7117525644510466049\ntype: Article\nlikeCount: 177\npostContent: New blog post on Microsoft Playwright Testing.",
    "Author: Charanjeet Kaur\nlikeCount: 32\npostContent: Sadagopan Rajaram is #hiring. Know anyone who might be interested?"
]
corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)

# -----------------------------
# 3. Define Retrieval Function
# -----------------------------
def your_retrieval_function(query):
    query_embedding = embedder.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=2)
    return [corpus[hit['corpus_id']] for hit in hits[0]]

# -----------------------------
# 4. Prompt Builder
# -----------------------------
FEW_SHOT = """
Example:
Post:
Author: Madhuri Jain
postUrl: https://linkedin.com/in/mjmadhu
likeCount: 940
postContent: Looking for a lawyer in Bangalore.

Q: How many followers does Madhuri Jain have?
A: Madhuri Jain has 940+ followers.

Q: What is the postContent for the post with postUrl 'https://linkedin.com/in/mjmadhu'?
A: Looking for a lawyer in Bangalore.
"""

def build_prompt_with_docs(query, docs):
    structured = "\n\n".join([f"Post {i+1}:\n{doc}" for i, doc in enumerate(docs)])
    return f"""{FEW_SHOT}

Posts:
{structured}

Q: {query}
A:"""

# -----------------------------
# 5. LLaMA Inference Function
# -----------------------------
def your_llama_generate(prompt):
    output = llm(prompt, max_tokens=150, stop=["Q:", "\n\n"])
    return output["choices"][0]["text"].strip()

# -----------------------------
# 6. Evaluation Metrics
# -----------------------------
def normalize_text(s):
    def remove_articles(text): return re.sub(r'\b(a|an|the)\b', ' ', text)
    def remove_punc(text): return re.sub(r'[^\w\s]', '', text)
    def white_space_fix(text): return ' '.join(text.split())
    return white_space_fix(remove_articles(remove_punc(s.lower())))

def exact_match_score(pred, truth):
    return normalize_text(pred) == normalize_text(truth)

def f1_score(pred, truth):
    pred_tokens = normalize_text(pred).split()
    truth_tokens = normalize_text(truth).split()
    common = Counter(pred_tokens) & Counter(truth_tokens)
    num_same = sum(common.values())
    if num_same == 0: return 0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(truth_tokens)
    return 2 * precision * recall / (precision + recall)

def bleu_score(pred, truth):
    reference = [normalize_text(truth).split()]
    candidate = normalize_text(pred).split()
    return sentence_bleu(reference, candidate)

def rouge_scores(pred, truth):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    return scorer.score(truth, pred)

# -----------------------------
# 7. Evaluate
# -----------------------------
test_data = [
    {
        "query": "How many followers does Madhuri Jain have?",
        "ground_truth": "Madhuri Jain has 940+ followers."
    },
    {
        "query": "What is the postContent for the post with postUrl 'https://linkedin.com/in/mjmadhu'?",
        "ground_truth": "Looking for a lawyer in Bangalore."
    },
    {
        "query": "Who is the author of the post mentioning 'Microsoft Playwright'?",
        "ground_truth": "Ashish Shah"
    },
    {
        "query": "What type of post is 'https://linkedin.com/feed/update/urn:li:activity:7117525644510466049'?",
        "ground_truth": "Article"
    }
]

exact_total = f1_total = bleu_total = rouge1_total = rougeL_total = 0

for item in test_data:
    query = item["query"]
    truth = item["ground_truth"]
    docs = your_retrieval_function(query)
    prompt = build_prompt_with_docs(query, docs)
    pred = your_llama_generate(prompt)

    print(f"\n🟡 Query: {query}\n✅ Ground Truth: {truth}\n🤖 Prediction: {pred}")

    exact_total += exact_match_score(pred, truth)
    f1_total += f1_score(pred, truth)
    bleu_total += bleu_score(pred, truth)
    rouge = rouge_scores(pred, truth)
    rouge1_total += rouge['rouge1'].fmeasure
    rougeL_total += rouge['rougeL'].fmeasure

n = len(test_data)
print("\n📊 Evaluation Results")

print(f"accuracy: {f1_total / n:.2f}")

c
