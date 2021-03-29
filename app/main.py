from typing import Optional
from fastapi import FastAPI
from loguru import logger
from scripts.es_functions import vector_query, standard_query
from scripts.general import load_spacy_model, neo4j_connect

app = FastAPI()

# functions
vector_index_name = "*sentence_vectors"

# standard match against sentence text
def es_sent(text):    
    body={
        # "from":from_val,
        "size": 5,
        "query": {
             "match": {
                "sent_text": {
                    "query": text     
                }
            }
        },
        "_source": ["doc_id","sent_num","sent_text"]
    }
    res = standard_query(index_name=vector_index_name,body=body)
    results = []
    if res:
        for r in res['hits']['hits']:
            if r["_score"] > 0.5:
                results.append(r)
    return results

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.get("/search/")
async def run_query(query: str, method: Optional[str] = None):   
    # standard match against sentence text
    res = es_sent(query)
    print(res)
    if method:
        return {"query": query, "method": method, "res":res}
    else:
        return {"query": query, "res": res}
    