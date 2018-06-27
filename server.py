# -*- coding: utf-8 -*-
from sys import argv
from flask import Flask, request, jsonify
from nextrip import NexTrip, demo


nt = NexTrip(debug='debug' in argv)
app = Flask(__name__)


class APIException(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(self)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {'message': self.message}


@app.errorhandler(APIException)
def exception_handler(exception):
    response = jsonify(exception.to_dict())
    response.status_code = exception.status_code
    return response


def format_api_exception(exception):
    raise APIException(
        'Internal error: {}: {}'.format(exception.__class__.__name__, exception),
        status_code=500)


@app.route('/demo')
def api_demo():
    required = ['route', 'stop', 'direction']
    try:
        values = [request.args[it] for it in required]
    except KeyError as e:
        raise APIException("Missing parameter '{}'".format(e.args[0]))
    try:
        return jsonify(demo(*values, session=nt))
    except Exception as e:
        raise APIException('Error: {}'.format(e.args[0]))


# Proxy the API with a cached layer

@app.route('/providers')
def api_providers():
    try:
        return jsonify(nt.providers(cache_bust='cache_bust' in request.args))
    except Exception as e:
        format_api_exception(e)


@app.route('/routes')
def api_routes():
    try:
        return jsonify(nt.routes(cache_bust='cache_bust' in request.args))
    except Exception as e:
        format_api_exception(e)


@app.route('/directions/<int:route>')
def api_directions(route):
    try:
        return jsonify(nt.directions(route, cache_bust='cache_bust' in request.args))
    except Exception as e:
        format_api_exception(e)


@app.route('/stops/<int:route>/<int:direction>')
def api_stops(route, direction):
    try:
        return jsonify(nt.stops(route, direction, cache_bust='cache_bust' in request.args))
    except Exception as e:
        format_api_exception(e)


@app.route('/departures/<int:stop_id>')
def api_departures(stop_id):
    try:
        return jsonify(nt.departures(stop_id, cache_bust='cache_bust' in request.args))
    except Exception as e:
        format_api_exception(e)


@app.route('/timepoint_departures/<int:route>/<int:direction>/<stop>')
def api_timepoint_departures(route, direction, stop):
    try:
        return jsonify(nt.timepoint_departures(
            route, direction, stop, cache_bust='cache_bust' in request.args))
    except Exception as e:
        format_api_exception(e)


@app.route('/vehicle_locations/<int:route>')
def api_vehicle_locations(route):
    try:
        return jsonify(nt.vehicle_locations(route))
    except Exception as e:
        format_api_exception(e)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
