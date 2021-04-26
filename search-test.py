from scripts.es_functions import combine_full_and_vector
from scripts.general import load_spacy_model
from loguru import logger
import pandas as pd
import numpy as np
import os


query = 'genome wide association studies'
vector_index_name = "use_*_sentence_vectors"

f = 'gwas-vec.npy'
if os.path.exists(f):
    logger.info(f'{f} done')
    test_vec = np.load(f)
else:
    nlp = load_spacy_model()
    doc = nlp(query)
    test_vec = doc.vector
    logger.info(test_vec)
    np.save(f,test_vec)

logger.info(len(test_vec))

res = combine_full_and_vector(index_name = vector_index_name, query_text=query, query_vector=test_vec)
for r in res["hits"]["hits"][0:5]:
    logger.info(r)