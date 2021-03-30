import pandas as pd
import json
from scripts.es_functions import vector_query, standard_query
from scripts.general import neo4j_connect
from loguru import logger

vector_index_name = "*_sentence_vectors"

session = neo4j_connect()

top_hits = 100

def output_to_people(output_list:list):
    query = """
        match 
            (p:Person)-[:PERSON_OUTPUT]-(o:Output) 
        WHERE
            o.id in {output_list} 
        RETURN 
            p.name as person_name,p.url as person_id, o.id as output_id;
    """.format(output_list=output_list)
    logger.info(query)
    data=session.run(query).data()
    df = pd.json_normalize(data)
    logger.info(f'\n{df}')
    return df


# standard match against sentence text
def es_sent(text:str):    
    logger.info(f'Running es_sent with {text}')
    body={
        # "from":from_val,
        "size": 1000,
        "query": {
             "match": {
                "sent_text": {
                    "query": text     
                }
            }
        },
        "_source": ["doc_id","sent_num","sent_text"],
            "indices_boost": [
        { "title_sentence_vectors": 1.5 },
        { "abstract_sentence_vectors": 1 }
    ]
    }
    res = standard_query(index_name=vector_index_name,body=body)
    logger.info(res)
    results = []
    output_list = []
    if res:
        for r in res['hits']['hits']:
            if r["_score"] > 0.5:
                results.append(r['_source'])
                output_list.append(r['_source']['doc_id'])
    if len(output_list)>0:
        op = output_to_people(list(set(output_list)))
        op_counts = json.loads(op[['person_name','person_id']].value_counts().nlargest(top_hits).to_json())
        logger.info(f'\n{op_counts}')
        return op_counts
    else:
        return []

def es_vec(nlp,text:str):
    doc = nlp(text)
    for sent in doc.sents:
        logger.info(sent)

        # vectors
        sent_vec = sent.vector
        res = vector_query(index_name=vector_index_name, query_vector=sent_vec)
        if res:
            logger.info(res[0])
            results = []
            output_list = []
            if res:
                for r in res:
                    if r["score"] > 0.5:
                        results.append(r)
                        output_list.append(r['url'])
            if len(output_list)>0:
                op = output_to_people(list(set(output_list)))
                op_counts = json.loads(op[['person_name','person_id']].value_counts().nlargest(top_hits).to_json())
                logger.info(f'\n{op_counts}')
                return op_counts
            else:
                return []
            
