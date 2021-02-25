from flask_restful import Resource
from .PropertyFinder2 import PropertyFinder


class PropertyFinderResource(Resource):

    def __init__(self):
        self.finder = PropertyFinder()

    def get(self):
        return self.finder.search()
