#!flask/bin/python

# Inspired from : https://github.com/D4-project/IPASN-History/blob/master/website/web/__init__.py
# If you are derouted by the lack of decorator, go there : https://stackoverflow.com/questions/17129573/can-i-use-external-methods-as-route-decorators-in-python-flask

# ==================== ------ STD LIBRARIES ------- ====================
import flask
import sys, os
import time
import pathlib
import logging

# ==================== ------ PERSONAL LIBRARIES ------- ====================
sys.path.append(os.path.abspath(os.path.pardir))
import carlhauser_server.Configuration.webservice_conf as webservice_conf
import carlhauser_server.Helpers.id_generator as id_generator


# ==================== ------ SERVER Flask API definition ------- ====================

class EndpointAction(object):

    def __init__(self, action):
        self.action = action
        # self.response = flask.Response("Welcome to carl-hauser", status=200, headers={})

    def __call__(self, *args):
        # Perform the action
        answer = self.action(*args)

        # Create the answer (bundle it in a correctly formatted HTTP answer)
        if isinstance(answer, str):
            # If it's a string, we bundle it has a HTML-like answer
            self.response = flask.Response(answer, status=200, headers={})
        else:
            # If it's something else (dict, ..) we jsonify and send it
            self.response = flask.jsonify(answer)

        # Send it
        return self.response


class FlaskAppWrapper(object):
    def __init__(self, name, conf: webservice_conf):
        # STD attributes
        self.conf = conf
        self.logger = logging.getLogger(__name__)

        # Specific attributes
        self.app = flask.Flask(name)

    def run(self):
        # Handle SLL Certificate, if they are provided = use them, else = self sign a certificate on the fly
        if self.conf.CERT_FILE is None or self.conf.KEY_FILE is None:
            self.logger.error(f"Provided CERT OR KEY file not found :  {self.conf.CERT_FILE} and {self.conf.KEY_FILE}")
            self.app.run(ssl_context='adhoc')
        else:
            self.logger.info(f"Provided CERT OR KEY file used : {self.conf.CERT_FILE} and {self.conf.KEY_FILE}")
            self.app.run(ssl_context=(str(self.conf.CERT_FILE), str(self.conf.KEY_FILE)))  # ssl_context='adhoc')

    def add_all_endpoints(self):
        # Add root endpoint
        self.add_endpoint(endpoint="/", endpoint_name="/", handler=self.ping)

        # Add action endpoints
        self.add_endpoint(endpoint="/add_picture", endpoint_name="/add_picture", handler=self.add_picture)
        self.add_endpoint(endpoint="/request_similar_picture", endpoint_name="/request_similar_picture", handler=self.request_similar_picture)
        self.add_endpoint(endpoint="/get_results", endpoint_name="/get_results", handler=self.get_results)

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None):
        self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(handler), methods=['GET', 'POST', 'PUT'])

    # ==================== ------ API Calls ------- ====================

    def ping(self, *args):
        result_json = {}
        result_json["Called_function"] = "ping"
        result_json = self.add_std_info(result_json)

        result_json["Status"] = "The API is ALIVE :)"
        # Note that "flask.request" is a global object, but is linked to the local context by flask. No worries :)

        return result_json
        # Test it with curl 127.0.0.1:5000

    def add_picture(self):
        result_json = {}
        result_json["Called_function"] = "add_picture"
        result_json = self.add_std_info(result_json)

        if flask.request.method == 'PUT':
            f = flask.request.files['image']

            # Compute input picture hash and convert to BMP
            f_hash = id_generator.get_SHA1(f)
            f_bmp = id_generator.convert_to_bmp(f)

            # TODO : Call add picture on redis

            # If the filename need to be used : secure_filename(f.filename)
            # DEBUG / f_bmp = id_generator.write_to_file(f_bmp, pathlib.Path('./' + str(f_hash) + ".bmp").resolve())

            result_json["Status"] = "Success"
            result_json["img_id"] = f_hash

        else:
            result_json["Status"] = "Failure"
            result_json["Error"] = "BAD METHOD : use PUT instead of GET, POST, ..."

        return result_json
        # Test it with curl 127.0.0.1:5000/add_pict

    def request_similar_picture(self):
        result_json = {}
        result_json["Called_function"] = "request_similar_picture"
        result_json = self.add_std_info(result_json)

        # Dummy action
        return result_json
        # Test it with curl 127.0.0.1:5000/request_similar_picture

    def get_results(self):
        result_json = {}
        result_json["Called_function"] = "get_results"
        result_json = self.add_std_info(result_json)

        # Dummy action
        return result_json
        # Test it with curl 127.0.0.1:5000/get_results

    def add_std_info(self, result_json):
        result_json["Call_method"] = flask.request.method  # 'GET' or 'POST' ...
        result_json["Call_time"] = time.ctime()  # 'GET' or 'POST' ...

        return result_json