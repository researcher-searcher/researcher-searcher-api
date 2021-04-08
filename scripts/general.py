import scispacy
import spacy
import numpy as np
from scipy.spatial import distance
from loguru import logger
from environs import Env

env = Env()
env.read_env()

GRAPH_HOST = env.str("GRAPH_HOST")
GRAPH_BOLT_PORT = env.str("GRAPH_BOLT_PORT")
GRAPH_USER = env.str("GRAPH_USER")
GRAPH_PASSWORD = env.str("GRAPH_PASSWORD")


def load_spacy_model():
    model_name = "en_core_web_trf"
    model_name = "en_core_web_lg"
    # Load English tokenizer, tagger, parser and NER
    logger.info(f"Loading spacy model {model_name}")
    nlp = spacy.load(model_name)
    # nlp = spacy.load("en_core_sci_scibert")
    # nlp = spacy.load("en_core_sci_lg")
    # nlp = spacy.load("en_ner_bionlp13cg_md")
    # nlp.add_pipe("abbreviation_detector")

    # add max length for transformer
    # if model_name == 'en_core_web_trf':
    #    nlp.max_length = 512
    # nlp.max_length=10000
    logger.info("Done...")
    return nlp


def neo4j_connect():
    from neo4j import GraphDatabase, basic_auth

    auth_token = basic_auth(GRAPH_USER, GRAPH_PASSWORD)
    driver = GraphDatabase.driver(
        "bolt://" + GRAPH_HOST + ":" + GRAPH_BOLT_PORT, auth=auth_token, encrypted=False
    )
    session = driver.session()
    return session
