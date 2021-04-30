import pandas as pd
import numpy as np
import json
import math
import collections
from scripts.es_functions import (
    vector_query,
    standard_query,
    mean_vector_query,
    filter_query,
    combine_full_and_vector,
    aaa_person
)
from scripts.general import neo4j_connect
from loguru import logger

vector_index_name = "use_*_sentence_vectors_filter"
person_index_name = "use_person_vectors_filter"
output_index_name = "use_output_vectors_filter"

session = neo4j_connect()

top_hits = 100


def person_info(id_list: list, node_property: str):
    query = """
        match 
            (o:Org)-[r:PERSON_ORG]-(p:Person)
        WHERE
            p.{property} in {id_list}
        AND
            o.type in ['academicschool','academicdepartment'] 
        RETURN 
            p.name as name, p.url as url, p.email as email, collect(o.name) as org;
    """.format(
        property=node_property, id_list=id_list
    )
    logger.info(query)
    data = session.run(query).data()
    df = pd.json_normalize(data)
    logger.info(f"\n{df.head()}")
    return df


def output_info(id_list: list, node_property: str):
    query = """
        match 
            (o:Output)
        WHERE
            o.{property} in {id_list} 
        RETURN 
            o.id as id, o.title as title, o.year as year;
    """.format(
        property=node_property, id_list=id_list
    )
    logger.info(query)
    data = session.run(query).data()
    df = pd.json_normalize(data)
    logger.info(f"\n{df.head()}")
    return df


def output_to_people(output_list: list):
    logger.info(f"output_to_people {len(output_list)}")
    query = """
        match 
            (org:Org)-[r:PERSON_ORG]-(p:Person)-[:PERSON_OUTPUT]-(o:Output) 
        WHERE
            o.id in {output_list} 
        AND
            org.type in ['academicschool','academicdepartment'] 
        RETURN 
            p.name as person_name, p.email as person_email, p.url as person_id, o.id as output_id, collect(org.name) as org;
    """.format(
        output_list=output_list
    )
    # logger.info(query)
    data = session.run(query).data()
    df = pd.json_normalize(data)
    # logger.info(f'\n{df}')
    return df


# if no restriction on top number, people who have lots of hits get penalised for those hits with lower scores
# to just use top hit, set top to 1
def weighted_average(data, top=5):
    # logger.info(data['person_name'])
    weights = list(data["weight"][:top])
    scores = list(data["score"][:top])
    weighted_avg = np.average(scores, weights=weights)
    #logger.info(weighted_avg)

    # factor in the number of sentence hits
    #weighted_avg = weighted_avg * math.sqrt(len(weights))
    weighted_avg = round(weighted_avg * len(weights)**(1./3.),3)
    #logger.info(f'{weighted_avg} {len(weights)**(1./3.)}')
    
    # weighted_avg = round(np.average( scores),3)
    # logger.info(f'weights {weights} scores {scores} wa {weighted_avg}')
    return weighted_avg


def convert_df_to_wa(results_df, person_df, doc_col):
    logger.info(results_df.shape)
    m = results_df.merge(person_df, left_on=doc_col, right_on="output_id")
    m.drop([doc_col], axis=1, inplace=True)
    # m['weight']=range(m.shape[0],0,-1)
    df_group = m.groupby(by=["person_id", "person_name", "person_email"])
    wa = df_group.apply(weighted_average)
    df = df_group.size().reset_index(name="count")
    logger.info(df.head())
    
    #create single list for orgs
    orgs = list(df_group["org"].apply(list))
    unique_orgs = []
    for o in orgs:
        unique_orgs.append(o[0])
    df['org'] = unique_orgs
    
    # add weighted average
    df["wa"] = list(wa)
    
    # create lists for each group
    df["weights"] = list(df_group["weight"].apply(list))
    df["scores"] = list(df_group["score"].apply(list))
    df["m_sent_num"] = list(df_group["sent_num"].apply(list))
    df["q_sent_num"] = list(df_group["q_sent_num"].apply(list))
    df["m_sent_text"] = list(df_group["sent_text"].apply(list))
    df["q_sent_text"] = list(df_group["q_sent_text"].apply(list))
    df["output"] = list(df_group["output_id"].apply(list))
    df["index"] = list(df_group["index"].apply(list))
    df["year"] = list(df_group["year"].apply(list))

    df.sort_values(by="wa", ascending=False, inplace=True)
    return df

# standard match against sentence text
def es_vec_sent(nlp, text: str, year_range: list):
    logger.info(f"Running es_sent with {text}")
    doc = nlp(text)
    q_sent_num = 0
    results = []
    output_list = []
    for sent in doc.sents:
        # check if sentence is suitable
        if len(sent.text.strip())<3:
            continue
        logger.info(f"##### {q_sent_num} {sent.text} ######")
        res = combine_full_and_vector(index_name=vector_index_name, query_vector=sent.vector, query_text=sent.text, year_range=year_range)
        # logger.info(res)
        if res:
            weight = len(res["hits"]["hits"])
            for r in res["hits"]["hits"]:
                rr = r["_source"]
                rr["index"] = r["_index"]
                rr["score"] = r["_score"]
                rr["q_sent_num"] = q_sent_num
                rr["q_sent_text"] = sent.text
                # square the weight to improve results for large number of hits
                rr["weight"] = weight
                results.append(rr)
                output_list.append(r["_source"]["doc_id"])
                weight -= 1
        q_sent_num += 1
    if len(output_list) > 0:
        logger.info(len(output_list))
        op = output_to_people(list(set(output_list)))
        es_df = pd.DataFrame(results)
        df = convert_df_to_wa(es_df, op, "doc_id")
        logger.info(f"\n{df.head(n=20)[['person_name','count','wa']]}")
        return df.to_dict("records")
    else:
        return []

# standard match against sentence text
def es_sent(nlp, text: str, year_range: list):
    logger.info(f"Running es_sent with {text}")
    doc = nlp(text)
    q_sent_num = 0
    results = []
    output_list = []
    for sent in doc.sents:
        # check if sentence is suitable
        if len(sent.text.strip())<3:
            continue
        logger.info(f"##### {q_sent_num} {sent.text} ######")
        res = standard_query(index_name=vector_index_name, text=sent.text, year_range=year_range)
        # logger.info(res)
        if res:
            weight = len(res["hits"]["hits"])
            for r in res["hits"]["hits"]:
                rr = r["_source"]
                rr["index"] = r["_index"]
                rr["score"] = r["_score"]
                rr["q_sent_num"] = q_sent_num
                rr["q_sent_text"] = sent.text
                # square the weight to improve results for large number of hits
                rr["weight"] = weight * weight
                results.append(rr)
                output_list.append(r["_source"]["doc_id"])
                weight -= 1
        q_sent_num += 1
    if len(output_list) > 0:
        logger.info(len(output_list))
        op = output_to_people(list(set(output_list)))
        es_df = pd.DataFrame(results)
        df = convert_df_to_wa(es_df, op, "doc_id")
        return df.to_dict("records")
    else:
        return []

def es_vec(nlp, text: str, year_range: list):
    doc = nlp(text)
    q_sent_num = 0
    results = []
    output_list = []
    for sent in doc.sents:
        # check if sentence is suitable
        if len(sent.text.strip())<3:
            continue
        logger.info(f"##### {q_sent_num} {sent} {len(sent.text.strip())} ######")
        # vectors
        sent_vec = sent.vector
        res = vector_query(index_name=vector_index_name, query_vector=sent_vec, year_range=year_range)
        #logger.info(res)
        if res:
            logger.info(res[0])
            weight = len(res)
            logger.info(weight)
            for r in res:
                r["q_sent_num"] = q_sent_num
                r["q_sent_text"] = sent.text
                # square the weight to improve results for large number of hits
                r["weight"] = weight
                results.append(r)
                output_list.append(r["url"])
                weight -= 1
        q_sent_num += 1
    if len(output_list) > 0:
        op = output_to_people(list(set(output_list)))
        es_df = pd.DataFrame(results)
        df = convert_df_to_wa(es_df, op, "url")
        return df.to_dict("records")
    else:
        return []

def get_vec(nlp,text:str,method:str):
    doc = nlp(text)
    logger.info(f"get_vec {text} {method}")
    results = []
    q_sent_num = 0

    if method == 'sent':
        for sent in doc.sents:
            # check if sentence is suitable
            if len(sent.text.strip())<3:
                continue
            logger.info(f"##### {q_sent_num} {sent} {len(sent.text.strip())} ######")
            # vectors
            vec = sent.vector
            results.append({
                'q_sent_num':q_sent_num,
                'q_sent_text':sent.text,
                'vector':vec.tolist()
            })
            q_sent_num += 1
    else:
        vec = doc.vector
        results.append({
                'q_sent_num':q_sent_num,
                'q_sent_text':text,
                'vector':vec.tolist()
            })
    #logger.info(results)
    return results


def es_person_vec(nlp, text: str):
    doc = nlp(text)
    logger.info(f"es_person_vec {text}")
    # vectors
    vec = doc.vector
    res = mean_vector_query(index_name=person_index_name, query_vector=vec)
    if res:
        logger.info(res[0])
        results = []
        output_list = []
        if res:
            for r in res:
                results.append(r)
                output_list.append(r["doc_id"])
        if len(output_list) > 0:
            es_df = pd.DataFrame(results)
            logger.info("here")
            logger.info(es_df.head())
            op = person_info(id_list=list(set(output_list)), node_property="email")
            m = es_df.merge(op, left_on="doc_id", right_on="email")
            m.drop(["doc_id"], axis=1, inplace=True)
            m.sort_values(by="score", ascending=False, inplace=True)
            logger.info(f"\n{m}")
            # op_counts = json.loads(op[['person_name','person_id']].value_counts().nlargest(top_hits).to_json())
            # logger.info(f'\n{op_counts}')
            return m.to_dict("records")
        else:
            return []


def es_output_vec(nlp, text: str):
    doc = nlp(text)
    logger.info(f"es_output_vec {text}")
    # vectors
    vec = doc.vector
    res = mean_vector_query(index_name=output_index_name, query_vector=vec)
    if res:
        logger.info(res[0])
        results = []
        output_list = []
        for r in res:
            results.append(r)
            output_list.append(r["doc_id"])
        if len(output_list) > 0:
            es_df = pd.DataFrame(results)
            logger.info("here")
            logger.info(es_df.head())
            op = output_info(id_list=list(set(output_list)), node_property="id")
            m = es_df.merge(op, left_on="doc_id", right_on="id")
            m.drop(["doc_id"], axis=1, inplace=True)
            m.sort_values(by="score", ascending=False, inplace=True)
            logger.info(f"\n{m}")
            # op_counts = json.loads(op[['person_name','person_id']].value_counts().nlargest(top_hits).to_json())
            # logger.info(f'\n{op_counts}')
            return m.to_dict("records")
        else:
            return []


def get_person_info(text: str, method: str = "fuzzy"):
    logger.info(f"get_person {text} {method}")
    if method == "fuzzy":
        query = """
            match 
                (p:Person)
            WHERE
                toLower(p.name) contains toLower('{text}') 
            RETURN 
                p.name as person_name,p.url as person_id;
        """.format(
            text=text
        )
    else:
        query = """
            match 
                (p:Person)
            WHERE
                p.name = '{text}' 
            RETURN 
                p.name as person_name,p.url as person_id;
        """.format(
            text=text
        )

    # logger.info(query)
    data = session.run(query).data()
    df = pd.json_normalize(data)
    # logger.info(f'\n{df}')
    return df


def get_collab(person: str, method: str):
    logger.info(f"get_collab {person} {method}")
    person = person.strip().lower()
    limit=100
    if method == "no":
        query = """
            MATCH 
                (p1:Person)-[pp:PERSON_PERSON]-(p2)-[r:PERSON_ORG]-(org:Org) 
            WHERE 
                p1._id = '{person}'
            AND
                org.type in ['academicschool','academicdepartment'] 
            WITH
                p1,pp,p2,org
            ORDER 
                by pp.score desc 
            LIMIT
                100
            MATCH 
                (p2) 
            WHERE 
                not (p1)-[:PERSON_OUTPUT]-(:Output)-[:PERSON_OUTPUT]-(p2) 
            RETURN
                p2.name as name, p2.email as email, p2.url as url, collect(org.name) as org, pp.score as score
            ORDER
                by score desc 
            LIMIT
                {limit}
        """.format(
            person=person,limit=limit
        )
    elif method == "yes":
        query = """
            MATCH 
                (p1:Person)-[pp:PERSON_PERSON]-(p2)-[r:PERSON_ORG]-(org:Org)  
            WHERE 
                p1._id = '{person}'
            AND
                org.type in ['academicschool','academicdepartment'] 
            WITH
                p1,pp,p2,org
            ORDER 
                by pp.score desc 
            LIMIT
                100
            MATCH 
                (p2) 
            WHERE 
                (p1)-[:PERSON_OUTPUT]-(:Output)-[:PERSON_OUTPUT]-(p2) 
            RETURN
                p2.name as name, p2.email as email, p2.url as url, collect(org.name) as org, pp.score as score 
            ORDER
                by score desc 
            LIMIT
                {limit}
        """.format(
            person=person,limit=limit
        )
    else:
        query = """
            MATCH 
                (p1:Person)-[pp:PERSON_PERSON]-(p2)-[r:PERSON_ORG]-(org:Org)
            WHERE
                org.type in ['academicschool','academicdepartment'] 
            AND 
                p1._id = '{person}'
            RETURN
                p2.name as name, p2.email as email, p2.url as url, collect(org.name) as org, pp.score as score 
            ORDER 
                by score desc 
            LIMIT
                {limit}
        """.format(
            person=person,limit=limit
        )
    logger.info(query)
    data = session.run(query).data()
    df = pd.json_normalize(data).to_dict("records")
    #logger.info(f"\n{df}")
    return df


def get_person(person: str, limit: int):
    logger.info(f"get_person {person}")
    person = person.strip().lower()
    query = """
        match 
            (p:Person)-[r]-(n:NounChunk) 
        where
            p._id = '{person}' 
        return 
            n.text as text,r.score as score order by r.score desc limit {limit};
    """.format(
        person=person,
        limit=limit
    )
    logger.info(query)
    data = session.run(query).data()
    if data:
        return data
    else:
        return []

def get_person_aaa(query:list):
    res = aaa_person(person_list=query)
    #logger.info(res)

