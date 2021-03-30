from typing import Optional
from fastapi import FastAPI
from loguru import logger
from scripts.es_functions import vector_query, standard_query
from scripts.general import load_spacy_model, neo4j_connect
from scripts.search import es_sent, es_vec

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
    if method == 'full':
        # standard match against sentence text
        res = es_sent(query)
        logger.info(res)
        return {"query": query, "method": method, "res":res}
    elif method == 'vec':
        # standard match against sentence text
        res = es_vec(nlp=nlp,text=query)
        logger.info(res)
        return {"query": query, "method": method, "res":res}
    else:
        return {"query": query, "res": 'NA'}
    