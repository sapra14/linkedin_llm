from huggingface_hub import hf_hub_download

# Download the model file to the current directory or your desired folder
model_path = hf_hub_download(
    repo_id="TheBloke/LLaMA-7b-GGUF",
    filename="llama-7b.Q4_K_M.gguf",
    local_dir="models",  # or "." if you want current directory
    local_dir_use_symlinks=False,
)

print(f"Model downloaded at: {model_path}")
