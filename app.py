import api.hello
from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from api.PropertyFinderResource import PropertyFinderResource

app = Flask(__name__)
CORS(app)

app.register_blueprint(api.hello.bp)
api = Api(app)
api.add_resource(PropertyFinderResource, '/search')

if __name__ == '__main__':
    app.run(port=12576)
