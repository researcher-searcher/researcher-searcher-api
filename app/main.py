from typing import Optional
from fastapi import FastAPI
from loguru import logger
from scripts.es_functions import vector_query, standard_query
from scripts.general import load_spacy_model, neo4j_connect
from scripts.search import es_sent, es_vec, get_person, get_colab, es_person_vec

app = FastAPI()

# globals
nlp = load_spacy_model()

@app.get("/")
def read_root():
    return {"Researcher Searcher"}

@app.get("/search/")
async def run_query(query: str, method: Optional[str] = None):   
    # standard match against query sentences
    if method == 'full':
        res = es_sent(nlp=nlp,text=query)
        #logger.info(res)
        return {"query": query, "method": method, "res":res}
    # sentence vector match against query sentences
    elif method == 'vec':
        res = es_vec(nlp=nlp,text=query)
        #logger.info(res)
        return {"query": query, "method": method, "res":res}
    # people vector match against query
    elif method == 'person':
        res = es_person_vec(nlp=nlp,text=query)
        #logger.info(res)
        return {"query": query, "method": method, "res":res}
    else:
        return {"query": query, "res": 'NA'}

@app.get("/colab/")
async def run_query(query: str, method: Optional[str] = None):   
    #if method == 'exact':
    #    person = get_person(text=query, method=method)
    #else:
    #    person = get_person(text=query)    
    colab = get_colab(query)
    return {"query": query, "method": method, "res":colab}
    

#todo
# sort results above using weighted mean or something similar.
# add collaboration recommender (closest person with no shared output)
# add output recommender (closest output to text)
    