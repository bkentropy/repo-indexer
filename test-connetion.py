
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
print(client.models.list())