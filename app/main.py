from typing import Optional
from fastapi import FastAPI
from loguru import logger
from scripts.es_functions import vector_query, standard_query
from scripts.general import load_spacy_model, neo4j_connect
from scripts.search import es_sent

app = FastAPI()

# globals
nlp = load_spacy_model()

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
    