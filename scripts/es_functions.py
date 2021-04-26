from elasticsearch import Elasticsearch
from elasticsearch import helpers
from collections import deque
from loguru import logger
import numpy as np
import time
import pandas as pd
from environs import Env

env = Env()
env.read_env()

ES_HOST = env.str("ES_HOST")
ES_PORT = env.str("ES_PORT")
ES_USER = env.str("ES_USER")
ES_PASSWORD = env.str("ES_PASSWORD")

TIMEOUT = 300
chunkSize = 10000
es = Elasticsearch(
    [f"{ES_HOST}:{ES_PORT}"], http_auth=(ES_USER, ES_PASSWORD), timeout=TIMEOUT
)

TITLE_WEIGHT = 1
ABSTRACT_WEIGHT = 0.95

def vector_query(
    index_name:str, query_vector:list, record_size:int=100000, search_size:int=100, score_min:int=0, year_range:list=[1950,2021]
):
    script_query = {
        "script_score": {
            "query": {
                "bool" : {
                "must" : [{
                    "match_all": {}
                },
                {
                    "range": {
                        "year": {
                        "from": year_range[0],
                        "to": year_range[1]
                        }
                    }
                }]
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
                    {"use_title_sentence_vectors": TITLE_WEIGHT},
                    {"use_abstract_sentence_vectors": ABSTRACT_WEIGHT},
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
            # print("id: {}, score: {}".format(hit["_id"], hit["_score"] - 1))
            # print(hit["_source"])
            # print()
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
    except:
        return []


def mean_vector_query(
    index_name:str, query_vector:list, record_size:int=100000, search_size:int=100, score_min:int=0
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
            # print("id: {}, score: {}".format(hit["_id"], hit["_score"] - 1))
            # print(hit["_source"])
            # print()
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


def standard_query(index_name:str, text:str, year_range:list=[1950,2021]):
    body = {
        "size": 100,
        "query": {
            "bool" : {
            "must" : [{
                "match": {
                    "sent_text": {
                        "query": text     
                    }
                }
            },
            {
                "range": {
                    "year": {
                    "from": year_range[0],
                    "to": year_range[1]
                    }
                }
            }]
            }
        },
        "_source": ["doc_id", "sent_num", "sent_text", "year"],
        "indices_boost": [
            {"use_title_sentence_vectors": TITLE_WEIGHT},
            {"use_abstract_sentence_vectors": ABSTRACT_WEIGHT},
        ],
    }
    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=index_name, body=body
    )
    return res


def filter_query(index_name:str, filterData:str):
    body = {
        # "from":from_val,
        "size": 10000,
        "query": {"bool": {"filter": filterData}},
    }

    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=index_name, body=body
    )
    return res

# https://discuss.elastic.co/t/use-distance-on-dense-vectors-in-relevance-score-at-query-time/217012/2
def combine_full_and_vector(index_name:str, query_text:str, query_vector:list, record_size:int=100000, search_size:int=100, score_min:int=0, year_range:list=[1950,2021]
):
    logger.info(query_text)
    body = {
        "size": 100,
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "sent_text": {
                                "query": query_text,     
                                #"boost" : 10
                            },                            
                        },
                         
                    },
                    {
                        "script_score": {
                            "query" : {"match_all" : {}},
                            "script":{
                                # +1 to deal with negative results (script score function must not produce negative scores)
                                "source": "50 * cosineSimilarity(params.query_vector, 'sent_vector') +1",
                                "params": {"query_vector": query_vector},
                            },
                            #"boost" : 100
                        },
                    },        
                ],
            }
        },
        "_source": ["doc_id", "sent_num", "sent_text", "year"],
        "indices_boost": [
            {"use_title_sentence_vectors": TITLE_WEIGHT},
            {"use_abstract_sentence_vectors": ABSTRACT_WEIGHT},
        ],
    }
    res = es.search(
        ignore_unavailable=True, request_timeout=TIMEOUT, index=index_name, body=body
    )
    return res