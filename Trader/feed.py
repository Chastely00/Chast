import pymongo as pm
import pandas as pd
from typing import Union
import datetime
import numpy as np

def get_from_mongo(elements: list, symbols: list=[], db:str='Fields',
    start: Union[datetime.datetime, None]=None, 
    end: Union[datetime.datetime, None]=None,
    concat: bool=False,
    ffill: list=[],
    zscore: list=[],
    pprint: bool=True,
    **kwards) -> Union[pd.DataFrame, dict]:
    """
    elements: Element, 表示要在Mongo中抓哪些資料, 須用list包起來
    symbols: 商品清單
    start: 開始時間, 若沒定義則會抓取沒有日期的資料
    end: 結束時間
    concat: 打開以後就會return一個大表，擁有multiindex的columns，level0是表單名稱(開盤價、收盤價等)
    """
    client = pm.MongoClient()
    if concat:
        df = pd.DataFrame()
    else:
        df = dict()
    symbols = {s: 1 for s in symbols}
    symbols['_id'] = 0
    if start == None:
        date = {}
    else:
        date = {'日期': {'$gte': start, '$lte': end}}
        if len(symbols) != 1:
            symbols['日期'] = 1

    for e in elements:
        data = pd.DataFrame(client[db][e].find(date, symbols))
        if '日期' in data.columns:
            data.set_index('日期', inplace=True)
        data = data.reindex(sorted(data.columns), axis=1)
        if pprint:
            print(f'Data {e} has shape {data.shape}')
        data.columns = pd.MultiIndex.from_tuples(tuple(zip([e]*len(data.columns), data.columns)))
        # 資料預先處理就放在**kwards裡
        if e in kwards: # 'Q': .rolling(4).sum()
            string = 'data'+kwards[e]
            data = eval(string)
        if e in zscore:
            data = (data.subtract(data.mean(axis=1), axis=0)).divide(data.std(ddof=0, axis=1), axis=0)
            data = data.mask(data>5, 5)
            data = data.mask(data<-5, -5)
        if concat:
            df = pd.concat([df, data], axis=1, join='outer')
        else:
            df[e] = data
    if concat:
        df.sort_index(inplace=True)
    for f in ffill:
        df.loc[:, f] = df.ffill()
    return df