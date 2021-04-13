from typing import Optional
from fastapi import Depends, FastAPI, Query
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
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
)
from enum import Enum

app = FastAPI(docs_url="/")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# globals
nlp = load_spacy_model()

# @app.get("/")
# def read_root():
#    return {"Researcher Searcher"}


class SearchMethods(str, Enum):
    f = "full"
    v = "vec"
    p = "person"
    o = "output"


class CollabFilter(str, Enum):
    y = "yes"
    n = "no"
    a = "all"


@app.get(
    "/search/",
    description=(
        "Search via a number of methods\n"
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
        SearchMethods.f,
        title="Search Method",
        description="the method to use for the search query (full, vec, person or output)",
    ),
    year_min: int = Query(
        1950,
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
    if method == "full":
        res = es_sent(nlp=nlp, text=query)
        return {"query": query, "method": method, "res": res, 'year_range':[year_min,year_max]}
    # sentence vector match against query sentences
    elif method == "vec":
        res = es_vec(nlp=nlp, text=query)
        return {"query": query, "method": method, "res": res}
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
        ..., title="Person Query", description="the email address of the person"
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
        description="the email address of the person",
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


# customise the swagger interface
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Bristol data science network API",
        version="0.1",
        description="",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
