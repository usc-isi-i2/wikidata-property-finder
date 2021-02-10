import numpy as np
import pandas as pd
from collections import defaultdict
from difflib import SequenceMatcher
from .settings import FILE_claims_count, FILE_qualifiers_count, FILE_total_count

class PropertyRanker(object):

    def __init__(self):
        ''' table_counts: stores the number of main values, qualifiers, and reference counts '''
        self.table_counts = self._build_table()

    def _build_table(self):

        claims_counts = pd.read_csv(FILE_claims_count, sep='\t', usecols=['node1','node2']).set_index('node1')
        claims_counts.columns = [['main value']]

        qualifier_counts = pd.read_csv(FILE_qualifiers_count, sep='\t', usecols=['node1','node2']).set_index('node1')
        qualifier_counts.columns = [['qualifier']]

        total_counts = pd.read_csv(FILE_total_count, sep='\t', usecols=['node1','node2']).set_index('node1')
        total_counts.columns = [['total']]

        glossory = pd.concat([claims_counts, qualifier_counts, total_counts], axis=1).fillna(0).astype(int)
        glossory.columns = [x[0] for x in glossory]
        glossory['both'] = glossory['main value'] + glossory['qualifier']

        glossory['p:main_value'] = glossory['main value'] / glossory['both']
        glossory['p:qualifier'] = 1.0 - glossory['p:main_value']

        return glossory

    def gen_counts(self, pnodes, scope='both'):
        counts = defaultdict(int)
        for node in pnodes:
            try:
                counts[node] = int(self.table_counts.loc[node][scope])
            except KeyError:
                counts[node] = 0
        return counts

    def gen_similarity(self, pnodes, query, metadata):
        sim = defaultdict(float)
        for node in pnodes:
            try:
                sim[node] = np.max([SequenceMatcher(None, query, n).ratio() for n in metadata.get_names(node)])
            except KeyError:
                sim[node] = 0.0
        return sim

    def rank(self, pnodes, query, metadata, scope='both'):

        ranking = defaultdict(float)
        counts = self.gen_counts(pnodes, scope)
        sim = self.gen_similarity(pnodes, query, metadata)

        for pnode in pnodes:
            ranking[pnode] = sim[pnode] * np.log(counts[pnode]+1)

        return dict(sorted(ranking.items(), key=lambda x:x[1], reverse=True))
