import streamlit as st
import csv
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def load_metadata():
    with open("raw_metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)

from linkedin_filter import apply_filters, format_results
from linkedin_query_answer import answer_linkedin_query

def main():
    st.set_page_config(page_title="LinkedIn Profile Assistant", page_icon="🔍", layout="wide")
    
    # CSS styles
    st.markdown("""
    <style>
    [data-testid="stColumn"] {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 30px;
        min-height: 400px;
        box-sizing: border-box;
    }
    [data-testid="stColumn"] h1, 
    [data-testid="stColumn"] h2, 
    [data-testid="stColumn"] h3, 
    [data-testid="stColumn"] label,
    [data-testid="stColumn"] .stTextInput > label,
    [data-testid="stColumn"] .stTextArea > label,
    [data-testid="stColumn"] .stMarkdown p {
        color: black !important;
    }
    .header-flex {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .title-centered {
        text-align: center;
        margin-bottom: 30px;
        font-weight: 700;
        font-size: 2.5rem;
        color: #333333;
    }
    .response-box {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 10px;
        padding: 20px;
        color: black;
        box-sizing: border-box;
        white-space: pre-wrap;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title-centered">Klype LinkedIn Profile Assistant</div>', unsafe_allow_html=True)

    metadata = load_metadata()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="header-flex"><h2>Query LinkedIn Posts</h2></div>', unsafe_allow_html=True)
        st.markdown("Ask a question or search LinkedIn post content directly")

        question = st.text_area(
            "Your question:",
            height=150,
            placeholder="E.g., How many followers does Madhuri Jain have?"
        )

        if question and question.strip():
            answer = answer_linkedin_query(metadata, question)
            if answer and "could not find" not in answer.lower():
                st.markdown("### LLM Answer:")
                st.markdown(f'<div class="response-box">{answer}</div>', unsafe_allow_html=True)
            else:
                filtered_results = apply_filters(metadata, question)
                if filtered_results:
                    st.markdown("### Filtered Results:")
                    formatted_text = format_results(filtered_results)
                    st.markdown(formatted_text, unsafe_allow_html=True)
                else:
                    st.warning("No matching results found.")
        else:
            st.info("Enter a question above to get answers or filtered results.")

    with col2:
        st.markdown('<div class="header-flex"><h2>Generate a LinkedIn Post</h2></div>', unsafe_allow_html=True)

        user_prompt = st.text_area(
            "Enter your prompt",
            height=150,
            placeholder="E.g., Write a post about transitioning into tech or career growth tips."
        )

        if st.button("Generate Post"):
            if not user_prompt.strip():
                st.warning("Please enter a valid prompt.")
            else:
                with st.spinner("Generating your post..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are a professional LinkedIn post writer."},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.7,
                            max_tokens=300
                        )
                        post_content = response.choices[0].message.content.strip()

                        st.markdown("### Generated Post")
                        st.markdown(f'<div class="response-box">{post_content}</div>', unsafe_allow_html=True)

                        # Save to CSV
                        with open("generated_linkedin_posts.csv", mode="a", newline='', encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow([user_prompt, post_content])
                        st.info("Post saved to generated_linkedin_posts.csv")

                    except Exception as e:
                        st.error(f"Error generating post: {e}")

if __name__ == "__main__":
    main()
