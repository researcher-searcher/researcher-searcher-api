from elasticsearch import Elasticsearch
from elasticsearch import helpers
from collections import deque
from app.logging import logger
import numpy as np
import time
import pandas as pd
from environs import Env
from scripts.general import create_aaa_distances

env = Env()
env.read_env()

ES_HOST = env.str("ELASTIC_HOST").strip()
ES_PORT = env.str("ELASTIC_PORT").strip()
ES_USER = env.str("ELASTIC_USER").strip()
ES_PASSWORD = env.str("ELASTIC_PASSWORD").strip()


TIMEOUT = 300
chunkSize = 10000
try:
    es = Elasticsearch(
        [f"{ES_HOST}:{ES_PORT}"], http_auth=(ES_USER, ES_PASSWORD), timeout=TIMEOUT
    )
except Exception as e:
    logger.error(f"Problem with ES connection {ES_HOST}:{ES_PORT} {ES_USER} {ES_PASSWORD}")
    logger.error(e)
    exit(1)
    

TITLE_WEIGHT = 1
ABSTRACT_WEIGHT = 1
ES_HIT_LIMIT = 100

PERSON_INDEX = "use_person_vectors"
OUTPUT_TITLE_INDEX = "use_title_sentence_vectors"
OUTPUT_ABSTRACT_INDEX = "use_abstract_sentence_vectors"

logger = logger.bind(debug=True)


def vector_query(
    index_name: str,
    query_vector: list,
    record_size: int = 100000,
    search_size: int = ES_HIT_LIMIT,
    score_min: int = 0,
    year_range: list = [1950, 2021],
):
    script_query = {
        "script_score": {
            "query": {
                "bool": {
                    "must": [
                        {"match_all": {}},
                        {
                            "range": {
                                "year": {"from": year_range[0], "to": year_range[1]}
                            }
                        },
                    ]
                }
            },
            "script": {
                # +1 to deal with negative results (script score function must not produce negative scores)
                "source": "cosineSimilarity(params.query_vector, 'sent_vector') +1",
                "params": {"query_vector": query_vector},
            },
        }
    }
    search_start = time.time()
    try:
        response = es.search(
            index=index_name,
            body={
                "size": search_size,
                "query": script_query,
                "_source": {"includes": ["doc_id", "year", "sent_num", "sent_text"]},
                "indices_boost": [
                    {OUTPUT_TITLE_INDEX: TITLE_WEIGHT},
                    {OUTPUT_ABSTRACT_INDEX: ABSTRACT_WEIGHT},
                ],
            },
        )
        search_time = time.time() - search_start
        logger.info(f'Total hits {response["hits"]["total"]["value"]}')
        logger.info(f"Search time: {search_time}")
        results = []
        for hit in response["hits"]["hits"]:
            # logger.debug(hit)
            # -1 to deal with +1 above
            # score cutoff
            if hit["_score"] - 1 > score_min:
                results.append(
                    {
                        "index": hit["_index"],
                        "url": hit["_source"]["doc_id"],
                        "year": hit["_source"]["year"],
                        "sent_num": hit["_source"]["sent_num"],
                        "sent_text": hit["_source"]["sent_text"],
                        "score": hit["_score"] - 1,
                    }
                )
        logger.debug(len(results))
        return results
    except Exception as e:
        logger.warning(e)
        return []


def mean_vector_query(
    index_name: str,
    query_vector: list,
    record_size: int = 100000,
    search_size: int = ES_HIT_LIMIT,
    score_min: int = 0,
):
    logger.debug(f"mean_vector_query {index_name}")
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                # +1 to deal with negative results (script score function must not produce negative scores)
                "source": "cosineSimilarity(params.query_vector, 'vector') +1",
                "params": {"query_vector": query_vector},
            },
        }
    }
    search_start = time.time()
    try:
        response = es.search(
            index=index_name,
            body={
                "size": search_size,
                "query": script_query,
                "_source": {"includes": ["doc_id"]},
            },
        )
        search_time = time.time() - search_start
        logger.info(f'Total hits {response["hits"]["total"]["value"]}')
        logger.info(f"Search time: {search_time}")
        results = []
        for hit in response["hits"]["hits"]:
            # logger.debug(hit)
            # -1 to deal with +1 above
            # score cutoff
            if hit["_score"] - 1 > score_min:
                results.append(
                    {
                        "index": hit["_index"],
                        "doc_id": hit["_source"]["doc_id"],
                        "score": hit["_score"] - 1,
                    }
                )
        return results
    except:
        logger.warning("ES search failed")
        return []


def standard_query(index_name: str, text: str, year_range: list = [1950, 2021]):
    body = {
        "size": ES_HIT_LIMIT,
        "query": {
            "bool": {
                "must": [
                    {"match": {"sent_text": {"query": text}}},
                    {"range": {"year": {"from": year_range[0], "to": year_range[1]}}},
                ]
            }
        },
        "_source": ["doc_id", "sent_num", "sent_text", "year"],
        "indices_boost": [
            {OUTPUT_TITLE_INDEX: TITLE_WEIGHT},
            {OUTPUT_ABSTRACT_INDEX: ABSTRACT_WEIGHT},
        ],
    }
    logger.info(body)
    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=index_name, body=body
    )
    return res


def filter_query(index_name: str, filterData: str):
    body = {
        # "from":from_val,
        "size": ES_HIT_LIMIT,
        "query": {"bool": {"filter": filterData}},
    }

    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=index_name, body=body
    )
    return res


# https://discuss.elastic.co/t/use-distance-on-dense-vectors-in-relevance-score-at-query-time/217012/2
def combine_full_and_vector(
    index_name: str,
    query_text: str,
    query_vector: list,
    record_size: int = 100000,
    search_size: int = 100,
    score_min: int = 0,
    year_range: list = [1950, 2021],
):
    logger.info(query_text)
    body = {
        "size": ES_HIT_LIMIT,
        "query": {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "sent_text": {
                                            "query": query_text,
                                            # "boost" : 10
                                        },
                                    }
                                },
                                {
                                    "range": {
                                        "year": {
                                            "from": year_range[0],
                                            "to": year_range[1],
                                        }
                                    }
                                },
                            ]
                        }
                    },
                    {
                        "script_score": {
                            # "query" : {"match_all" : {}},
                            "query": {
                                "range": {
                                    "year": {"from": year_range[0], "to": year_range[1]}
                                }
                            },
                            "script": {
                                # +1 to deal with negative results (script score function must not produce negative scores)
                                "source": "cosineSimilarity(params.query_vector, 'sent_vector') +1",
                                "params": {"query_vector": query_vector},
                            },
                            "boost": 10,
                        },
                    },
                ],
            }
        },
        "_source": ["doc_id", "sent_num", "sent_text", "year"],
        "indices_boost": [
            {OUTPUT_TITLE_INDEX: TITLE_WEIGHT},
            {OUTPUT_ABSTRACT_INDEX: ABSTRACT_WEIGHT},
        ],
    }
    # logger.info(body)
    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=index_name, body=body
    )
    return res


def aaa_person(person_list: list):
    logger.info(person_list)

    # get vectors for each person
    body = {
        "size": ES_HIT_LIMIT,
        "query": {"bool": {"filter": [{"terms": {"doc_id": person_list}}]}},
        "_source": ["doc_id", "vector"],
    }
    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=PERSON_INDEX, body=body
    )
    # logger.info(res)

    # create dictionary of IDs and vectors
    vector_data = {}
    for r in res["hits"]["hits"]:
        person_id = r["_source"]["doc_id"]
        person_vector = r["_source"]["vector"]
        vector_data[person_id] = person_vector
    logger.info(len(vector_data))

    # run aaa cosine
    pws = create_aaa_distances(list(vector_data.values()))
    logger.info(pws)

    # create df of person-person and score
    aaa_data = []
    for i, key1 in enumerate(vector_data):
        for j, key2 in enumerate(vector_data):
            # logger.info(f'{key1} {key2} {pws[i][j]}')
            aaa_data.append({"p1": key1, "p2": key2, "score": 1 - pws[i][j]})
    df = pd.DataFrame(aaa_data)
    logger.info(df)
    return df
