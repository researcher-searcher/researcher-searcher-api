from loguru import logger
from functools import reduce
import pandas as pd
import numpy as np


def weighted_average(data):
    # logger.info(data['person_name'])
    weights = list(data["weight"])
    scores = list(data["score"])
    weighted_avg = round(np.average(scores, weights=weights), 3)
    # logger.info(f'weights {weights} scores {scores} wa {weighted_avg}')
    return weighted_avg
    # return reduce(lambda x, y: x + y, series)


df = pd.read_csv("vec.tsv", sep="\t")
df.sort_values(by="score", ascending=False, inplace=True)
logger.info(f"\n{df.columns}")
logger.info(f"\n{df[['person_id','sent_num']]}")
df["weight"] = range(df.shape[0], 0, -1)
# group by person
df_group = df.groupby(by=["person_id", "person_name"])
# create weighted average
wa = df_group.apply(weighted_average)
# convert to df
df_group_df = df_group.size().reset_index(name="count")
logger.info(df_group_df.columns)
# add wa
df_group_df["wa"] = list(wa)
# create list of sentence numbers
sent_list = list(df_group["sent_num"].apply(list))
output_list = list(df_group["output_id"].apply(list))
logger.info(sent_list)
df_group_df["sent"] = sent_list
df_group_df["output"] = output_list
# df_group_df['sent_num']=df_group['sent_num']
df_group_df.sort_values(by="wa", ascending=False, inplace=True)
logger.info(df_group_df[["person_name", "count", "wa"]])
df_group_df.to_csv("test.tsv", sep="\t")
