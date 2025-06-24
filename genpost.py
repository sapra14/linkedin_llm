from llama_cpp import Llama

MODEL_PATH = "models/llama-7b.Q4_K_M.gguf"

print(f"Loading model from: {MODEL_PATH} ...")
llm = Llama(model_path=MODEL_PATH)
print("Model loaded successfully!")

def generate_linkedin_post(user_input: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional LinkedIn post writer. "
                "Write a friendly, engaging, and clear LinkedIn post based on the user's input. "
                "Avoid repetition and use varied sentence structures."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    response = llm.chat_completion(
        messages=messages,
        max_tokens=400,
        temperature=0.7,
        top_p=0.9,
    )

    post = response.choices[0].message["content"].strip()
    return post


if __name__ == "__main__":
    print("Welcome to LinkedIn Post Generator (type 'exit' to quit)")
    while True:
        user_input = input("\nEnter your achievement/event for LinkedIn post: ")
        if user_input.strip().lower() == "exit":
            print("Exiting... Goodbye!")
            break
        post = generate_linkedin_post(user_input)
        if post:
            print("\n📢 Suggested LinkedIn Post:\n", post)
        else:
            print("⚠️ Warning: The model returned empty output. Try again with a different input.")
