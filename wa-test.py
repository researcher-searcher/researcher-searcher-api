from loguru import logger
from functools import reduce
import pandas as pd
import numpy as np

def weighted_average(data):
    logger.info(data['person_name'])
    weights = list(data['weight'])
    scores = list(data['score'])
    weighted_avg = round(np.average( scores, weights = weights),3)
    logger.info(f'weights {weights} scores {scores} wa {weighted_avg}')
    return weighted_avg
    #return reduce(lambda x, y: x + y, series) 

df = pd.read_csv('vec.tsv',sep='\t')
df['weight']=range(df.shape[0],0,-1)
logger.info(df.columns)
logger.info(df[['weight','score']])
df_group = df.groupby(by='person_name')
wa=df_group.apply(weighted_average)
logger.info(wa)
df_group = df_group.size().reset_index(name='count')
df_group['wa']=list(wa)
logger.info(df_group[['person_name','count','wa']])
