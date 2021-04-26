from scripts.es_functions import combine_full_and_vector, standard_query, vector_query
from scripts.general import load_spacy_model
from loguru import logger
import pandas as pd
import numpy as np
import os


query = 'genome wide association studies'
query = 'Systematic reviews of genetic association'
query = 'what are the risk factors for breast cancer?'

vector_index_name = "use_*_sentence_vectors"

f = query.replace(' ','_')+'.npy'
if os.path.exists(f):
    logger.info(f'{f} done')
    test_vec = np.load(f)
else:
    logger.info('Running NLP')
    nlp = load_spacy_model()
    doc = nlp(query)
    test_vec = doc.vector
    logger.info(test_vec)
    np.save(f,test_vec)

logger.info(len(test_vec))

top = 10

logger.info('### COMBINED')
res1 = combine_full_and_vector(index_name = vector_index_name, query_text=query, query_vector=test_vec)
d = []
for r in res1["hits"]["hits"][0:top]:
    rr = r['_source']
    rr['index'] = r['_index']
    rr['score'] = r['_score']
    d.append(rr)
df1 = pd.DataFrame(d)
logger.info(f'\n{df1[["index","sent_text","score"]]}')

logger.info('### FULL TEXT')
res2 = standard_query(index_name=vector_index_name,text=query) 
d = []
for r in res2["hits"]["hits"][0:top]:
    rr = r['_source']
    rr['score'] = r['_score']
    rr['index'] = r['_index']
    d.append(rr)
df2 = pd.DataFrame(d)
try:
    logger.info(f'\n{df2[["index","sent_text","score"]]}')
except:
    logger.info('No data')

logger.info('### VECTOR')
res3 = vector_query(index_name=vector_index_name,query_vector=test_vec)
df3 = pd.DataFrame(res3[0:top])
logger.info(f'\n{df3[["index","sent_text","score"]]}')
