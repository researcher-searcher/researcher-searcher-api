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
es = Elasticsearch([f'{ES_HOST}:{ES_PORT}'], http_auth=(ES_USER, ES_PASSWORD), timeout=TIMEOUT)


def create_vector_index(index_name, dim_size):
    if es.indices.exists(index_name, request_timeout=TIMEOUT):
        print("Index name already exists, please choose another")
    else:
        request_body = {
            "settings": {
                "number_of_shards": 5,
                "number_of_replicas": 0,
                "refresh_interval": -1,
                "index.max_result_window": 100000,
            },
            "mappings": {
                "dynamic": "true",
                "_source": {"enabled": "true"},
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "year": {"type": "integer"},
                    "sent_id": {"type": "keyword"},
                    "sent_text": {"type": "text"},
                    "sent_vector": {"type": "dense_vector", "dims": dim_size},
                },
            },
        }
        res = es.indices.create(
            index=index_name, body=request_body, request_timeout=TIMEOUT
        )
        logger.info(res)


def create_noun_index(index_name, dim_size):
    if es.indices.exists(index_name, request_timeout=TIMEOUT):
        print("Index name already exists, please choose another")
    else:
        request_body = {
            "settings": {
                "number_of_shards": 5,
                "number_of_replicas": 0,
                "refresh_interval": -1,
                "index.max_result_window": 100000,
            },
            "mappings": {
                "dynamic": "true",
                "_source": {"enabled": "true"},
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "year": {"type": "integer"},
                    "sent_num": {"type": "keyword"},
                    "noun_phrase": {"type": "text"},
                },
            },
        }
        logger.info(f"Creating index {index_name}")
        res = es.indices.create(
            index=index_name, body=request_body, request_timeout=TIMEOUT
        )
        logger.info(res)


def index_vector_data(df, index_name):
    print("Indexing data...")
    # create_index(index_name)
    bulk_data = []
    counter = 1
    start = time.time()

    for i, rows in df.iterrows():
        # with gzip.open(sentence_data) as f:
        # next(f)
        counter += 1
        if counter % 1000 == 0:
            end = time.time()
            t = round((end - start), 4)
            print(len(bulk_data), t, counter)
        if counter % chunkSize == 0:
            deque(
                helpers.streaming_bulk(
                    client=es,
                    actions=bulk_data,
                    chunk_size=chunkSize,
                    request_timeout=TIMEOUT,
                    raise_on_error=True,
                ),
                maxlen=0,
            )
            bulk_data = []
        # print(line.decode('utf-8'))
        if np.count_nonzero(rows["vector"]) == 0:
            #logger.info(
            #    f"{rows['url']} {rows['sent_num']} returned empty vector so skipping"
            #)
            continue
        else:
            data_dict = {
                "doc_id": rows["url"],
                "year": rows["year"],
                "sent_num": rows["sent_num"],
                "sent_text": rows["sent_text"],
                "sent_vector": rows["vector"],
            }
            op_dict = {
                "_index": index_name,
                "_source": data_dict,
            }
            bulk_data.append(op_dict)
    print(len(bulk_data))
    deque(
        helpers.streaming_bulk(
            client=es,
            actions=bulk_data,
            chunk_size=chunkSize,
            request_timeout=TIMEOUT,
            raise_on_error=True,
        ),
        maxlen=0,
    )

    # check number of records, doesn't work very well with low refresh rate
    print("Counting number of records...")
    try:
        es.indices.refresh(index=index_name, request_timeout=TIMEOUT)
        res = es.search(index=index_name, request_timeout=TIMEOUT)
        esRecords = res["hits"]["total"]
        print("Number of records in index", index_name, "=", esRecords)
    except TIMEOUT:
        print("counting index timeout", index_name)

def index_noun_data(df, index_name):
    print("Indexing data...")
    # create_index(index_name)
    bulk_data = []
    counter = 1
    start = time.time()

    for i, rows in df.iterrows():
        # with gzip.open(sentence_data) as f:
        # next(f)
        counter += 1
        if counter % 1000 == 0:
            end = time.time()
            t = round((end - start), 4)
            print(len(bulk_data), t, counter)
        if counter % chunkSize == 0:
            deque(
                helpers.streaming_bulk(
                    client=es,
                    actions=bulk_data,
                    chunk_size=chunkSize,
                    request_timeout=TIMEOUT,
                    raise_on_error=True,
                ),
                maxlen=0,
            )
            bulk_data = []
        data_dict = {
            "doc_id": rows["url"],
            "year": rows["year"],
            "sent_num": rows["sent_num"],
            "noun_phrase": rows["noun_phrase"]
        }
        op_dict = {
            "_index": index_name,
            "_source": data_dict,
        }
        bulk_data.append(op_dict)
    print(len(bulk_data))
    deque(
        helpers.streaming_bulk(
            client=es,
            actions=bulk_data,
            chunk_size=chunkSize,
            request_timeout=TIMEOUT,
            raise_on_error=True,
        ),
        maxlen=0,
    )

    # check number of records, doesn't work very well with low refresh rate
    print("Counting number of records...")
    try:
        es.indices.refresh(index=index_name, request_timeout=TIMEOUT)
        res = es.search(index=index_name, request_timeout=TIMEOUT)
        esRecords = res["hits"]["total"]
        print("Number of records in index", index_name, "=", esRecords)
    except TIMEOUT:
        print("counting index timeout", index_name)

def delete_index(index_name):
    logger.info(f"Deleting {index_name}")
    if es.indices.exists(index_name, request_timeout=TIMEOUT):
        res = es.indices.delete(index=index_name, request_timeout=TIMEOUT)
        logger.info(res)
    else:
        logger.info(f"{index_name} does not exist")


def vector_query(
    index_name, query_vector, record_size=100000, search_size=100, score_min=0
):
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                # +1 to deal with negative results (script score function must not produce negative scores)
                "source": "cosineSimilarity(params.query_vector, doc['sent_vector']) +1",
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
                    { "title_sentence_vectors": 1 },
                    { "abstract_sentence_vectors": 0.75 }
                ]
            },
        )
        search_time = time.time() - search_start
        logger.info(f'Total hits {response["hits"]["total"]["value"]}')
        logger.info(f"Search time: {search_time}")
        results = []
        for hit in response["hits"]["hits"]:
            #logger.debug(hit)
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
        return results
    except:
        return []

def mean_vector_query(
    index_name, query_vector, record_size=100000, search_size=100, score_min=0
):
    logger.debug(f"mean_vector_query {index_name}")
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                # +1 to deal with negative results (script score function must not produce negative scores)
                "source": "cosineSimilarity(params.query_vector, doc['vector']) +1",
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
                "_source": {"includes": ["doc_id"]}
            },
        )
        search_time = time.time() - search_start
        logger.info(f'Total hits {response["hits"]["total"]["value"]}')
        logger.info(f"Search time: {search_time}")
        results = []
        for hit in response["hits"]["hits"]:
            #logger.debug(hit)
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
        logger.warning('ES search failed')
        return []

def standard_query(
    index_name, body
):
    res = es.search(
        ignore_unavailable=True,
        request_timeout=TIMEOUT,
        index=index_name,
        body=body
    )
    return res