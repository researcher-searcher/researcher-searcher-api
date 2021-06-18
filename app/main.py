from typing import Optional
from fastapi import Depends, FastAPI, Query
from fastapi.openapi.utils import get_openapi
#from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from scripts.general import load_spacy_model, neo4j_connect
from scripts.search import (
    es_sent,
    es_vec,
    get_person,
    get_collab,
    es_person_vec,
    es_output_vec,
    get_person,
    get_vec,
    es_vec_sent,
    get_person_aaa
)
from enum import Enum

app = FastAPI(docs_url="/")
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# globals
nlp = load_spacy_model()

# @app.get("/")
# def read_root():
#    return {"Researcher Searcher"}


class SearchMethods(str, Enum):
    c = "combine"
    f = "full"
    v = "vec"
    p = "person"
    o = "output"


class CollabFilter(str, Enum):
    y = "yes"
    n = "no"
    a = "all"

class SplitMethod(str, Enum):
    sent = "sent"
    all = "all"


@app.get(
    "/search/",
    description=(
        "Search via a number of methods\n"
        "- for a person, using vector embedding and sentence text (combine)\n"
        "- for a person, using sentence text (full)\n"
        "- for a person, using vector embedding of sentences (vec)\n"
        "- for a person, using mean vector (person)\n"
        "- for an output, using mean vector (output)"
    ),
    tags=["search"],
)
async def run_search(
    query: str = Query(
        ...,
        title="Search Query",
        description="the text to use for the search query",
        min_length=3,
        max_length=10000,
    ),
    method: SearchMethods = Query(
        SearchMethods.c,
        title="Search Method",
        description="the method to use for the search query (full, vec, person or output)",
    ),
    year_min: int = Query(
        2000,
        title="Minimum year",
        description="minimum year of output",
        ge=1950
    ),
    year_max: int = Query(
        2021,
        title="Maximum year",
        description="maximum year of output",
        le=2021
    ),
    # token: str = Depends(oauth2_scheme)
):
    # standard match against query sentences
    if method == "combine":
        res = es_vec_sent(nlp=nlp, text=query, year_range=[year_min, year_max])
        return {"query": query, "method": method, 'year_range':[year_min,year_max], "res": res}
    if method == "full":
        res = es_sent(nlp=nlp, text=query, year_range=[year_min, year_max])
        return {"query": query, "method": method, 'year_range':[year_min,year_max], "res": res}
    # sentence vector match against query sentences
    elif method == "vec":
        res = es_vec(nlp=nlp, text=query, year_range=[year_min, year_max])
        return {"query": query, "method": method, 'year_range':[year_min,year_max], "res": res}
    # people vector match against query
    elif method == "person":
        res = es_person_vec(nlp=nlp, text=query)
        return {"query": query, "method": method, "res": res}
    # output vector match against query
    elif method == "output":
        res = es_output_vec(nlp=nlp, text=query)
        return {"query": query, "method": method, "res": res}
    else:
        return {"query": query, "res": "NA"}


@app.get(
    "/person/",
    description=("Get a summary of noun chunks for a given person"),
    tags=["search"],
)
async def run_person(
    query: str = Query(
        ..., title="Person Query", description="the id of the person"
    ),
    limit: int = Query(
        10,
        title="Number of results to return",
        description="number of results to return",
        le=100
    ),
):
    data = get_person(query,limit)
    return {"query": query, "res": data}


@app.get(
    "/collab/",
    description=(
        "For a given person, find the people who are 'most similar' "
        "with optional co-publication filter"
    ),
    tags=["search"],
)
async def run_collab(
    query: str = Query(
        ...,
        title="Collaboration recommender",
        description="the id of the person",
    ),
    method: CollabFilter = Query(
        CollabFilter.y,
        title="Shared output filter",
        description="restrict results to those with shared output (yes), without (no) or all (all)",
    ),
    # token: str = Depends(oauth2_scheme)
):
    data = get_collab(query, method)
    return {"query": query, "method": method, "res": data}

@app.get(
    "/vector/",
    description=("Create a vector representation for a piece of text"),
    tags=["search"],
)
async def run_vector(
    query: str = Query(
        ..., title="Vector Query", description="the text to use for the search query"
    ),
    method: SplitMethod = Query(
        SplitMethod.sent,
        title="Split on sentence or whole text",
        description="create a vector for each sentence (sent) or for the whole text (all)",
    ),
):
    data = get_vec(nlp=nlp,text=query,method=method)
    return {"query": query, "method":method, "res": data}

@app.get(
    "/aaa/",
    description=("Return all against all distance calculations for list of people"),
    tags=["search"],
)
async def run_person_aaa(
    query: list = Query(
        ..., title="Person list", description="list of people IDs"
    )
):
    data = get_person_aaa(query=query)
    return {"query": query, "res": data}

# customise the swagger interface
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Researcher Searcher - Bristol Medical School (PHS) API",
        version="0.1",
        description="",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
