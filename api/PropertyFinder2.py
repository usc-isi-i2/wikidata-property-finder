import json, wordninja
import pandas as pd
from requests import get
from collections import defaultdict
from math import isnan, nan

from flask import request
from time import time

from .metadata import PropertyMetaData
from .ranking import PropertyRanker
from .settings import FILE_claims_property, JSON_constraints, KGTK_search

import warnings
warnings.filterwarnings("ignore")

class PropertyFinder(object):

    metadata = PropertyMetaData()
    ranker = PropertyRanker()

    def __init__(self, host=KGTK_search,
                        metadata_constraints=JSON_constraints,
                        query_size=500, use_ninja=True, use_part=True):
        self.host = host

        self.map_P1696 = self.gen_relation('P1696')
        self.map_P1647 = self.gen_relation('P1647', False)
        self.map_P6609 = self.gen_relation('P6609', False)
        self.map_P1659 = self.gen_relation('P1659')

        with open(metadata_constraints) as fp:
            self.constraints = json.load(fp)

        self.query_size = query_size
        self.ninja = use_ninja
        self.partial_query = use_part

    def _query(self, label, type_=None):
        ''' Given a query string: label,
            get relevant properties from the KGTK-search API
        '''
        response2 = get(f'{self.host}/{label}?extra_info=true&language=en&item=property&type=ngram&size={self.query_size}&instance_of=', verify=False)
        query_result = set([x['qnode'] for x in response2.json()])

        try:
            # Split word using wordninja
            if len(query_result) == 0 and self.ninja:
                label_splitted = ' '.join([x[:10] for x in wordninja.split(label)])
                response2 = get(f'{self.host}/{label_splitted}?extra_info=true&language=en&item=property&type=ngram&size={self.query_size}&instance_of=', verify=False)
                for x in response2.json():
                    query_result.add(x['qnode'])


                # Use a part of the input as the query string
                if len(query_result) == 0 and self.partial_query:

                    label_splitted = [x[:10] for x in wordninja.split(label)]

                    response2a = get(f'{self.host}/{label_splitted[0]}?extra_info=true&language=en&item=property&type=ngram&size={self.query_size}&instance_of=', verify=False)
                    for x in response2a.json():
                        query_result.add(x['qnode'])

                    response2b = get(f'{self.host}/{label_splitted[-1]}?extra_info=true&language=en&item=property&type=ngram&size={self.query_size}&instance_of=', verify=False)
                    for x in response2b.json():
                        query_result.add(x['qnode'])

                    if len(label_splitted) > 2:

                        response2c = get(f'{self.host}/{label_splitted[0]+label_splitted[1]}?extra_info=true&language=en&item=property&type=ngram&size={self.query_size}&instance_of=', verify=False)
                        for x in response2c.json():
                            query_result.add(x['qnode'])

                        response2d = get(f'{self.host}/{label_splitted[-2]+label_splitted[-1]}?extra_info=true&language=en&item=property&type=ngram&size={self.query_size}&instance_of=', verify=False)
                        for x in response2d.json():
                            query_result.add(x['qnode'])
        except:
            return []

        if type_:
            return [x for x in query_result if PropertyFinder.metadata.check_property_exists(x) and PropertyFinder.metadata.check_type(x, type_)]

        return [x for x in query_result]

    def filter_by_set(self, s, l):
        ''' Return all the unique values in l,
                save all the values to set s
        '''
        r = [i for i in l if not i in s]
        r = list(set(r))
        for i in r:
            s.add(i)
        return s, r

    def gen_relation(self, label, twoway=True):
        ''' Given a relation R, generate the triples such that
            X R Y, containing all X, Y that satisfying this relation
        '''
        pr = pd.read_csv(FILE_claims_property, sep='\t', usecols=['node1','label','node2'])
        pr = pr[pr['label'].apply(lambda x: x == label)].reset_index(drop=True)
        pr = pr[['node1', 'node2']]

        pr1 = pr.groupby('node1')['node2'].apply(list).reset_index()
        pr_dict = pr1.set_index('node1').to_dict()['node2']

        pr_dict_r = defaultdict(list)
        for k, v in pr_dict.items():
            for vi in v:
                pr_dict_r[k].append(vi)

        return pr_dict_r

    def get_candidates(self, name_, type_):
        ''' Get all the candidates given a query string: name_, and the specified type_
            Returns: Dict[List]
            1 -> properties whose label/aliases matches with query string
            2 -> relevant properties to category (1), using P1696, P1647, P6609
            3 -> relevant properties to category (1), using P1659
        '''
        result = self._query(name_, type_)

        ranked = {}
        loaded = set()
        loaded, ranked[1] = self.filter_by_set(loaded, result)

        ranked[2] = []
        for z in result:
            ranked[2] += self.map_P1696[z] + self.map_P1647[z] + self.map_P6609[z]
        loaded, ranked[2] = self.filter_by_set(loaded, ranked[2])

        ranked[3] = []
        for z in result:
            ranked[3] += self.map_P1659[z]
        loaded, ranked[3] = self.filter_by_set(loaded, ranked[3])

        if type_ is None:
            return ranked

        r = {}
        r[0] = []
        for i, L in enumerate(ranked):
            r[i+1] = []
            for pnode in ranked[L]:
                if PropertyFinder.metadata.check_type(pnode, type_):
                    r[i+1].append(pnode)

        r[4] = []

        return r

    def filter_ranked(self, ranked, params):
        ''' Rule-based filtering
            Using several wikidata constraints
        '''
        ranked = self.filter_by_item(ranked)

        if params['scope'] != 'both':
            ranked = self.filter_by_scope(ranked, params['scope'])

        ranked = self.filter_by_allowed_qualifiers(ranked, params['constraint'])
        ranked = self.filter_by_required_qualifiers(ranked, params['constraint'])

        ranked = self.filter_by_conflicts(ranked, params['otherProperties'])
        return ranked

    def filter_by_item(self, ranked):

        r = defaultdict(list)
        for k, pnodes in ranked.items():
            for pnode in pnodes:
                if pnode in self.constraints and 'noitem' in self.constraints[pnode]:
                    continue
                r[k].append(pnode)
        return r

    def filter_by_scope(self, ranked, scope='both'):

        r = defaultdict(list)
        for k, pnodes in ranked.items():
            for pnode in pnodes:

                if not pnode in self.constraints:
                    r[k].append(pnode)
                    continue

                info = self.constraints[pnode]
                if scope == 'qualifier':
                    if 'scope' in info and not 'Q' in info['scope']:
                        if 'scope_man' in info:
                            continue
                        r[4].append(pnode)
                        continue
                else:
                    if 'scope' in info and not 'V' in info['scope']:
                        if 'scope_man' in info:
                            continue
                        r[4].append(pnode)
                        continue
                r[k].append(pnode)

        return r

    def filter_by_allowed_qualifiers(self, ranked, constraint):


        if constraint is None:
            return ranked

        if not constraint in self.constraints:
            return ranked

        constr_dic = self.constraints[constraint]

        if not 'allowed_qualifiers' in constr_dic:
            return ranked

        r = defaultdict(list)
        for k, pnodes in ranked.items():
            for pnode in pnodes:
                if not pnode in constr_dic['allowed_qualifiers']:
                    continue
                r[k].append(pnode)

        return r

    def filter_by_required_qualifiers(self, ranked, constraint):

        if constraint is None:
            return ranked

        if not constraint in self.constraints:
            return ranked

        constr_dic = self.constraints[constraint]

        if not 'required_qualifiers' in constr_dic:
            return ranked

        r = defaultdict(list)
        for k, pnodes in ranked.items():
            for pnode in pnodes:
                if pnode in constr_dic['required_qualifiers']:
                    r[0].append(pnode)
                    continue
                r[k].append(pnode)

        return r

    def filter_by_conflicts(self, ranked, otherProperties):

        if otherProperties == '':
            return ranked

        properties = otherProperties.split(',')
        disallowed = set()
        for pnode in properties:
            if pnode in self.constraints and 'conflicts' in self.constraints[pnode]:
                for p in self.constraints[pnode]['conflicts']:
                    disallowed.add(p)

        r = defaultdict(list)
        for k, pnodes in ranked.items():
            for pnode in pnodes:
                if pnode in disallowed:
                    continue
                r[k].append(pnode)

        return r


    def find_property(self, label, params):

        params['type'] = PropertyFinder.metadata.get_type_alias(params['type'])

        candidates = self.get_candidates(label, params['type'])

        if params['filter']:
            candidates = self.filter_ranked(candidates, params)

        for level in candidates:
            candidates[level] = PropertyFinder.ranker.rank(candidates[level], label, PropertyFinder.metadata, scope=params['scope'])

        return dict(sorted(candidates.items(), key=lambda x: x[0]))

    def generate_top_candidates(self, params, size=10):
        ''' argument params may include the following parameters:
            type
            scope
            filter
            constraint
            otherProperties
        '''

        if not 'type' in params:
            params['type'] = None
        if not 'scope' in params:
            params['scope'] = 'both'
        if not 'filter' in params:
            params['filter'] = True
        if not 'constraint' in params:
            params['constraint'] = None
        if not 'otherProperties'  in params:
            params['otherProperties'] = ''

        label = params.pop('label')

        candidates = self.find_property(label, params)

        results = []
        for level in candidates:
            for pnode, score in candidates[level].items():

                results.append(PropertyFinder.metadata.get_info(pnode, score))
                if len(results) >= size:
                    break

            if len(results) >= size:
                break

        return results

    def _build_params(self, label, type_, scope='both', filter='true', constraint=None, otherProperties=''):
        ''' Build the dictionary of parameters
        '''
        return {'label': label,
                'type': type_,
                'scope': scope,
                'filter': filter=='true',
                'constraint': constraint,
                'otherProperties': otherProperties }

    def search(self):
        ''' Flask API interface
        '''
        label = request.args.get('label', '')
        if label == '':
            return {'Error': 'label (query string) needed. Please enter the following parameter ?label=xxx'}, 400

        type_ = request.args.get('data_type', None)

        if not type_ is None and not PropertyFinder.metadata.check_type_allowed(type_):
            return {'Error': 'Input data_type is not supported'}, 400

        # Check remote is running
        response = get(f'{self.host}/time?extra_info=true&language=en&item=property&type=ngram&size=1&instance_of=', verify=False)
        if response.status_code >= 500:
            return {'Error': 'Remote service for querying properties is down.'}, 500

        scope = request.args.get('scope', 'both')
        filter = request.args.get('filter', 'true')
        constraint = request.args.get('constraint', None)
        otherProperties = request.args.get('otherProperties', '')
        size = request.args.get('size', 10)

        try:
            size = int(size)
        except:
            return {'Error': 'size parameter must be an integer'}, 400

        params = self._build_params(label, type_, scope, filter, constraint, otherProperties)

        return self.generate_top_candidates(params, size)
