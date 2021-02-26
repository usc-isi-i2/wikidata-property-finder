from requests import get
from collections import defaultdict
from tqdm import tqdm
import pandas as pd
import json

es_url = 'http://ckg06.isi.edu:9200'
es_index = 'wikidataos-07'

if __name__ == '__main__':

    metadata = defaultdict(dict)

    df = pd.read_csv('data/labels.property.en.tsv.gz', usecols=['node1'],
                     sep='\t')
    for pnode in tqdm(df['node1']):
        res = get(f'{es_url}/{es_index}/_doc/{pnode}').json()
        try:
            metadata[pnode]['pagerank'] = res['_source']['pagerank']
        except:
            print(pnode, 'no pagerank')
            metadata[pnode]['pagerank'] = 0.0
        try:
            metadata[pnode]['statements'] = res['_source']['statements']
        except:
            print(pnode, 'no statements')
            metadata[pnode]['statements'] = 1

    with open('data/metadata.json', 'w') as fd:
        json.dump(metadata, fd, indent=2)
