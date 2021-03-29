from typing import Optional
from fastapi import FastAPI
from scripts.es_functions import vector_query, standard_query
from scripts.general import load_spacy_model, neo4j_connect

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.get("/search/")
async def run_query(query: str, method: Optional[str] = None):   
    if method:
        return {"query": query, "method": method}
    else:
        return {"query": query}
    