import pandas as pd
import json
from scripts.es_functions import vector_query, standard_query, mean_vector_query
from scripts.general import neo4j_connect
from loguru import logger

vector_index_name = "*_sentence_vectors"
person_index_name = "person_vectors"
output_index_name = "output_vectors"

session = neo4j_connect()

top_hits = 100

def person_info(id_list:list,node_property:str):
    query = """
        match 
            (p:Person)
        WHERE
            p.{property} in {id_list} 
        RETURN 
            p.name as name, p.url as url, p.email as email;
    """.format(property=node_property,id_list=id_list)
    logger.info(query)
    data=session.run(query).data()
    df = pd.json_normalize(data)
    logger.info(f'\n{df.head()}')
    return df


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

def es_person_vec(nlp,text:str):
    doc = nlp(text)
    logger.info(f'es_person_vec {text}')
    # vectors
    vec = doc.vector
    res = mean_vector_query(index_name=person_index_name, query_vector=vec)
    if res:
        logger.info(res[0])
        results = []
        output_list = []
        if res:
            for r in res:
                if r["score"] > 0.5:
                    results.append(r)
                    output_list.append(r['doc_id'])
        if len(output_list)>0:
            es_df = pd.DataFrame(results)
            logger.info('here')
            logger.info(es_df.head())
            op = person_info(id_list=list(set(output_list)),node_property='email')
            m = es_df.merge(op,left_on='doc_id',right_on='email')
            m.drop(['index'],axis=1,inplace=True)
            logger.info(f'\n{m}')
            #op_counts = json.loads(op[['person_name','person_id']].value_counts().nlargest(top_hits).to_json())
            #logger.info(f'\n{op_counts}')
            return m.to_dict('records')
        else:
            return []
            
def get_person(text:str,method:str='fuzzy'):
    logger.info(f'get_person {text} {method}')
    if method == 'fuzzy':
        query = """
            match 
                (p:Person)
            WHERE
                toLower(p.name) contains toLower('{text}') 
            RETURN 
                p.name as person_name,p.url as person_id;
        """.format(text=text)
    else:
        query = """
            match 
                (p:Person)
            WHERE
                p.name = '{text}' 
            RETURN 
                p.name as person_name,p.url as person_id;
        """.format(text=text)
        
    logger.info(query)
    data=session.run(query).data()
    df = pd.json_normalize(data)
    logger.info(f'\n{df}')
    return df

def get_colab(person:str):
    logger.info(f'get_colab {person}')
    query = """
        MATCH 
            (p1:Person)-[pp:PERSON_PERSON]-(p2) 
        WHERE 
            p1.url = '{person}'
        WITH
            p1,pp,p2 
        ORDER 
            by pp.score desc 
        LIMIT
            1000 
        MATCH 
            (p2) 
        WHERE 
            not (p1)-[:PERSON_OUTPUT]-(:Output)-[:PERSON_OUTPUT]-(p2) 
        RETURN
            p2.name as name,p2.url as url,pp.score as score 
        ORDER
            by score desc 
        LIMIT
            10
    """.format(person=person)
    logger.info(query)
    data=session.run(query).data()
    df = pd.json_normalize(data).to_dict('records')
    logger.info(f'\n{df}')
    return df