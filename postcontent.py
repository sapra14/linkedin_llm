import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Get API key from env variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set!")

client = OpenAI(api_key=api_key)

# Load CSV with LinkedIn posts
csv_path = "/Users/sunitasapra/linkedin_llm_project/data/merged_profiles.csv"
df = pd.read_csv(csv_path)
df = df.dropna(subset=["postContent"])

# Sample 3 posts for prompt (reduce sample size for test)
sample_posts = df["postContent"].sample(n=min(3, len(df))).tolist()

# Build prompt
prompt = f"""
You are a LinkedIn content creator. Here are some sample posts:

{''.join([f"- {post}\n" for post in sample_posts])}

Please write a new, unique, professional LinkedIn post inspired by these themes. Maximum 120 words.
"""

# Call OpenAI chat completions
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a professional LinkedIn content writer."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=300
)

generated_post = response.choices[0].message.content.strip()

print("\n📝 Generated LinkedIn Post:\n")
print(generated_post)
