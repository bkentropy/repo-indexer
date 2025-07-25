import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from dotenv import load_dotenv
from openai import OpenAI
import asyncio

load_dotenv()

INFERENCE_MODEL = os.getenv("OPENAI_MODEL", "/Users/bkustra/.ai-navigator/models/microsoft/Phi-3-mini-4k-instruct/Phi-3-Mini-4K-Instruct_Q8_0.gguf")
client = OpenAI(
    # base_url=os.getenv("OPENAI_HOST", "http://localhost:8084"),
    # api_key=os.getenv("OPENAI_API_KEY", "ai-nav")
    base_url=os.getenv("OPENAI_HOST", "http://localhost:1234/v1"),
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
    prompt_1 = f"""You are a helpful code assistant. Please analyze the following code snippets
    and provide a concise summary of their key functionality and relevance to the query: "{query}".

    Provide a single summary that captures the essence of the code snippets.

    Code snippets:
    """
    prompt_2 = """Please analyze the following code snippets.
    Provide a single summary that captures the essence of the code snippets, and a code example if you can.
    Code snippets:
    """
    prompt_3 = """Please analyze the following code snippets.
    Provide a single summary that captures the essence of the code snippets.
    Brief is better than long.
    Code snippets:
    """
    prompt = prompt_3

    for idx, result in enumerate(top_results, 1):
        prompt += f"\n\n## Code Snippet {idx}\n\nFile: {result.get('file_path', 'Unknown')} Type: {result.get('type', 'Unknown')} \n{result.get('code', '')}"

    try:
        response = query_model(prompt)

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating summary: {str(e)}"


async def summarize_code_stream(results, query):
    """
    Stream the summarization of the top 3 search results using an OpenAI-compatible model.

    Args:
        results (list): List of search results
        query (str): The original search query

    Yields:
        str: Chunks of the summary as they're generated
    """
    if not results:
        yield "No results found for the search query."
        return

    # Take top 3 results
    top_results = results[:3]

    # Create a prompt for summarization
    prompt_3 = """Please analyze the following code snippets.
    Provide a single summary that captures the essence of the code snippets.
    Brief is better than long.
    Code snippets:
    """
    prompt = prompt_3

    for idx, result in enumerate(top_results, 1):
        prompt += f"\n\n## Code Snippet {idx}\n\nFile: {result.get('file_path', 'Unknown')} Type: {result.get('type', 'Unknown')} \n{result.get('code', '')}"

    try:
        async for chunk in query_model_stream(prompt):
            yield chunk

    except Exception as e:
        yield f"Error generating summary: {str(e)}"


### helpers
def query_model(prompt):
    return client.chat.completions.create(
            model=INFERENCE_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful code assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

async def query_model_stream(prompt):
    """Stream the model response chunk by chunk."""
    try:
        stream = client.chat.completions.create(
            model=INFERENCE_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful code assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"Error in streaming: {str(e)}"

def get_content(response):
    return response.choices[0].message.content