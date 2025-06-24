import pandas as pd
from openai import OpenAI

client = OpenAI(
    api_key="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"  # your full key here
)

df = pd.read_csv("/Users/sunitasapra/linkedin_llm_project/data/merged_profiles.csv")
df['engagement'] = df['likeCount'] + df['commentCount']
df = df[df['postContent'].notnull()]
top_posts = df.sort_values(by='engagement', ascending=False).head(3)

top_post_samples = "\n\n".join(
    [f"{i+1}. {post}" for i, post in enumerate(top_posts['postContent'].tolist())]
)

prompt = f"""
You are an expert LinkedIn content strategist.

Here are 3 of my top-performing LinkedIn posts:

{top_post_samples}

🎯 Task: Based on tone, structure, and topics of these posts, generate 3 brand-new engaging LinkedIn posts that I can share. 
Make them fresh, professional, and aligned with my audience's interests. Vary the styles slightly: 
- One inspirational/motivational post
- One professional/achievement-based
- One opinion/thought-leadership post

Keep each post under 150 words.
"""

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant for writing LinkedIn content."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=700
)

print("\n🆕 Suggested LinkedIn Posts:\n")
print(response.choices[0].message.content)
