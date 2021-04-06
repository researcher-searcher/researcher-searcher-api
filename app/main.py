from typing import Optional
from fastapi import FastAPI
from loguru import logger
from scripts.general import load_spacy_model, neo4j_connect
from scripts.search import es_sent, es_vec, get_person, get_colab, es_person_vec, es_output_vec, get_person

app = FastAPI()

# globals
nlp = load_spacy_model()

@app.get("/")
def read_root():
    return {"Researcher Searcher"}

@app.get("/search/")
async def run_search(query: str, method: Optional[str] = None):   
    # standard match against query sentences
    if method == 'full':
        res = es_sent(nlp=nlp,text=query)
        return {"query": query, "method": method, "res":res}
    # sentence vector match against query sentences
    elif method == 'vec':
        res = es_vec(nlp=nlp,text=query)
        return {"query": query, "method": method, "res":res}
    # people vector match against query
    elif method == 'person':
        res = es_person_vec(nlp=nlp,text=query)
        return {"query": query, "method": method, "res":res}
    # output vector match against query
    elif method == 'output':
        res = es_output_vec(nlp=nlp,text=query)
        return {"query": query, "method": method, "res":res}
    else:
        return {"query": query, "res": 'NA'}

@app.get("/person/")
async def run_person(query: str, method: Optional[str] = None):
    data = get_person(query)
    return {"query": query, "method": method, "res":data}
  

@app.get("/colab/")
async def run_colab(query: str, method: Optional[str] = None):   
    #if method == 'exact':
    #    person = get_person(text=query, method=method)
    #else:
    #    person = get_person(text=query)    
    data = get_colab(query)
    return {"query": query, "method": method, "res":data}
    

#todo
# sort results above using weighted mean or something similar.
# add collaboration recommender (closest person with no shared output)
# add output recommender (closest output to text)
    