import pandas as pd
import math, json
from requests import get
from .settings import FILE_label, FILE_alias, FILE_description, FILE_datatype, FILE_metadata

allowed_types = ['commonsMedia', 'wikibase-item', 'external-id', 'url', 'string',
                 'quantity', 'time', 'globe-coordinate', 'monolingualtext',
                 'wikibase-property', 'math', 'geo-shape', 'tabular-data',
                 'wikibase-lexeme', 'wikibase-form', 'wikibase-sense',
                 'musical-notation']

type_aliases = {'media': 'commonsMedia', 'item': 'wikibase-item', 'id': 'external-id', 'coordinate': 'globe-coordinate',
                'property': 'wikibase-property', 'lexeme': 'wikibase-lexeme', 'form': 'wikibase-form',
                'sense': 'wikibase-sense',
                'country': 'wikibase-item', 'location': 'wikibase-item'}


class PropertyMetaData(object):

    def __init__(self):

        self.name_table = self._build_names()
        with open(FILE_metadata) as fd:
            self.remote_metadata = json.load(fd)

    def _build_names(self):
        ''' Build a table that includes the following information
        label, aliases, description, datatype,
        '''
        labels = pd.read_csv(FILE_label, sep='\t')
        labels['node2'] = labels['node2'].apply(lambda x: x[1:-4])
        labels.columns = ['pnode', 'label']
        labels = labels.groupby('pnode')['label'].apply(list).reset_index().set_index('pnode')

        aliases = pd.read_csv(FILE_alias, sep='\t')
        aliases['node2'] = aliases['node2'].apply(lambda x: x[1:-4])
        aliases.columns = ['pnode', 'alias']
        aliases = aliases.groupby('pnode')['alias'].apply(list).reset_index().set_index('pnode')

        description = pd.read_csv(FILE_description, sep='\t')
        description['node2'] = description['node2'].apply(lambda x: x[1:-4])
        description.columns = ['pnode', 'description']
        description = description.set_index('pnode')

        data_type = pd.read_csv(FILE_datatype, sep='\t', usecols=['node1', 'node2'])
        data_type.columns = ['pnode', 'data_type']
        data_type = data_type.set_index('pnode')

        merged = pd.concat([labels, aliases, description, data_type], axis=1)
        for row in merged.loc[merged.alias.isnull(), 'alias'].index:
            merged.at[row, 'alias'] = []

        return merged

    def get_info(self, pnode, score=0.0, extra_info=False, warning=[]):
        ''' Return the properties according to the required format
        '''
        dic = {'qnode': pnode,
               'description': [self.name_table.loc[pnode]['description']]
        }
        if extra_info:
            dic['label'] = self.name_table.loc[pnode]['label']
            dic['alias'] = self.name_table.loc[pnode]['alias']
            dic['pagerank'] = self.remote_metadata[pnode]['pagerank']
            dic['statements'] = self.remote_metadata[pnode]['statements']
            dic['score'] = score
            dic['data_type'] = self.name_table.loc[pnode]['data_type']

        return dic

    def get_label(self, pnode):
        return self.name_table.loc[pnode]['label'][0]

    def get_names(self, pnode):
        for name in self.name_table.loc[pnode]['label']:
            yield name
        for alias in self.name_table.loc[pnode]['alias']:
            yield alias

    def get_type(self, pnode):
        return self.name_table.loc[pnode]['data_type']

    def get_type_alias(self, type_):
        if type_ in type_aliases:
            type_ = type_aliases[type_]
        return type_

    def check_property_exists(self, pnode):
        try:
            self.name_table.loc[pnode]
            return True
        except KeyError:
            return False

    def check_type(self, pnode, type_):
        return self.get_type_alias(type_) == self.get_type(pnode)

    def check_type_allowed(self, type_):
        return type_ in allowed_types or type_ in type_aliases
