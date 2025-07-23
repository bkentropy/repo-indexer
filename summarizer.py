import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# INFERENCE_MODEL = os.getenv("OPENAI_MODEL", "openhermes-2.5-mistral-7b")
INFERENCE_MODEL = os.getenv("OPENAI_MODEL", "/Users/bkustra/.ai-navigator/models/microsoft/Phi-3-mini-4k-instruct/Phi-3-Mini-4K-Instruct_Q8_0.gguf")
client = OpenAI(
    base_url=os.getenv("OPENAI_HOST", "http://localhost:8084"),
    api_key=os.getenv("OPENAI_API_KEY", "lmstudio")
)

def summarize_code(results, query):
    """
    Summarize the top 3 search results using an OpenAI-compatible model.

    Args:
        results (list): List of search results
        query (str): The original search query

    Returns:
        str: Summary of the top results
    """
    if not results:
        return "No results found for the search query."

    # Take top 3 results
    top_results = results[:3]

    # Create a prompt for summarization
    prompt_old = f"""You are a helpful code assistant. Please analyze the following code snippets
    and provide a concise summary of their key functionality and relevance to the query: "{query}".

    Provide a single summary that captures the essence of the code snippets.

    Code snippets:
    """
    prompt = """Please analyze the following code snippets.
    Provide a single summary that captures the essence of the code snippets, and a code example if you can.
    Code snippets:
    """

    for idx, result in enumerate(top_results, 1):
        prompt += f"\n\n## Code Snippet {idx}\n\nFile: {result.get('file_path', 'Unknown')} Type: {result.get('type', 'Unknown')} \n{result.get('code', '')}"

    try:
        response = client.chat.completions.create(
            model=INFERENCE_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful code assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating summary: {str(e)}"
