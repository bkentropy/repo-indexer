import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from embedding_model import ModelCache

load_dotenv()
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
try:
    es = Elasticsearch(ES_HOST)
    if not es.ping():
        raise ValueError(f"Connection to Elasticsearch at {ES_HOST} failed.")
except Exception as e:
    raise RuntimeError(f"Error connecting to Elasticsearch: {e}")
INDEX_NAME = "code_chunks"

def ensure_index():
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body={ # type: ignore
            "mappings": {
                "properties": {
                    "embedding": {"type": "dense_vector", "dims": 384},
                    "code": {"type": "text"},
                    "name": {"type": "keyword"},
                    "type": {"type": "keyword"},
                    "file_path": {"type": "keyword"},
                    "repo": {"type": "keyword"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                }
            }
        })

def index_chunks(chunks: list):
    for chunk in chunks:
        es.index(index=INDEX_NAME, document=chunk)

def search_by_text(query: str, top_k: int = 5):
    model = ModelCache()
    query_vector = model.encode(query).tolist()

    # body = {
    #     "size": top_k,
    #     "query": {
    #         "script_score": {
    #             "query": {"match_all": {}},
    #             "script": {
    #                 "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
    #                 "params": {"query_vector": query_vector}
    #             }
    #         }
    #     }
    # }

    body = {
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": top_k,
                }
            }
        },
        "size": top_k
    }
    results = es.search(index=INDEX_NAME, body=body) # type: ignore
    return [hit["_source"] for hit in results["hits"]["hits"]]
