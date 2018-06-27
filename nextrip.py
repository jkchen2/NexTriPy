"""
.. _reference: http://svc.metrotransit.org/

A NexTrip API wrapper. See the NexTrip API `reference`_ for more information.
"""

import logging
import json
import time
import urllib.request

from enum import IntEnum
from functools import wraps
from typing import Union, Callable


__version__ = '1.0.1'

# Cache lifespan constants in seconds
GENERAL_CACHE_LIFESPAN = 3600
DEPARTURES_CACHE_LIFESPAN = 30

DEBUG = False


class CacheEntry:
    """
    A cache entry object that contains cached data, a lifespan, and a
    property that returns whether or not the entry has expired.
    """

    class CacheExpiredException(Exception):
        """Thrown if an entry was expired upon retrieval."""
        def __init__(self):
            super().__init__('cache entry expired')

    def __init__(self, lifespan: int, *, initial=None, debug=False):
        """
        Creates a cache entry with the given lifespan.

        :param lifespan: number of seconds until the cache data expires
        :param initial: initial data to add to the cache
        """
        # Debug
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[CE]: %(message)s'))
        self._logger = logging.getLogger(str(id(self)))
        self._logger.addHandler(handler)
        if debug:
            self._logger.setLevel(logging.DEBUG)

        self._data = initial
        self.last_fetched = time.time() if initial else 0
        self.lifespan = lifespan

    @property
    def data(self):
        """The entry's cached data value"""
        if self.expired:
            self._logger.debug("cache entry expired (last_fetched %s)", self.last_fetched)
            raise self.CacheExpiredException
        return self._data

    @data.setter
    def data(self, new_data):
        self.last_fetched = time.time()
        self._data = new_data
        self._logger.debug("cache data set (last_fetched %s)", self.last_fetched)

    @property
    def expired(self) -> bool:
        """Whether or not the cache entry has expired"""
        return time.time() - self.last_fetched > self.lifespan

    def hook(self, cache_bust: bool, callback: Callable, *args, **kwargs) -> 'CacheEntry':
        """
        :param cache_bust: forces the callback to be made, overwriting any cached data
        :param callback: the function to be called with ``args`` and ``kwargs``

        :Returns: the entry's data. If it has expired, it will be updated first
            with the return value of the callback. Additional (positional) arguments
            are used as parameters for the callback if it is needed.
        """
        if self.expired or cache_bust:
            self._logger.debug("using callback (last_fetched %s)", self.last_fetched)
            self.data = callback(*args, **kwargs)
        return self.data


class NexTrip:
    """
    .. |route ID| replace:: :meth:`route ID <routes>`
    .. |direction| replace:: :class:`direction <NexTrip.Directions>`
    .. |stop ID| replace:: `stop ID <https://gisdata.mn.gov/dataset/
        us-mn-state-metc-trans-transit-schedule-google-fd>`__

    A NexTrip API wrapper object.

    This provides coverage of all of the endpoints available and respects
    the caching requests as stated on the NexTrip API `reference`_.

    The return types of these endpoint methods are those returned by ``json.loads``.

    This will raise `urllib <https://docs.python.org/3/library/urllib.error.html>`_ and
    `json <https://docs.python.org/3/library/json.html#exceptions>`_ exceptions.

    More information regarding return types and constants can be found in the `reference`_.

    .. note::
        All endpoint methods that include a ``cache_bust`` keyword argument provide
        the option to bypass the cache by setting it to ``True``.

    Example usage:
        .. code-block:: python
            :linenos:

            # Create a NexTrip wrapper object
            from nextrip import NexTrip
            nt = NexTrip()

            # METRO Blue cardinal directions
            dirs = nt.directions(901)

            # Get stops in the first direction provided
            stops = nt.stops(901, dirs[0]['Value'])

            # Print the last stop's code and name
            print('{0[Value]}: {0[Text]}'.format(stops[-1]))

    For a more extensive example, see the :func:`demo` source code.
    """

    class Directions(IntEnum):
        """
        Integer enumeration of available cardinal directions.
        These are defined on the NexTrip API `reference`_.
        """
        SOUTH, EAST, WEST, NORTH = range(1, 5)  # Why

        def __str__(self):
            return str(self.value)

    _base = 'http://svc.metrotransit.org/NexTrip/'
    _headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    def __init__(self, *, debug=False):
        """Creates a NexTrip API wrapper object with caches."""
        # Debug
        self._use_debug = debug
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[NT]: %(message)s'))
        self._logger = logging.getLogger(str(id(self)))
        self._logger.addHandler(handler)
        if debug:
            self._logger.setLevel(logging.DEBUG)

        self._providers_cache = CacheEntry(GENERAL_CACHE_LIFESPAN, debug=self._use_debug)
        self._routes_cache = CacheEntry(GENERAL_CACHE_LIFESPAN, debug=self._use_debug)
        self._directions_cache = {}
        self._stops_cache = {}
        self._departures_cache = {}
        self._timepoint_departures_cache = {}

    @staticmethod
    def _get_cache_key(*args):
        """Creates a cache key from the given arguments."""
        return ':::'.join(str(it) for it in args)

    def _endpoint_method(method):
        """Adds logging calls to each endpoint method"""
        @wraps(method)
        def _decorated(self, *args, **kwargs):
            self._logger.debug("getting %s", method.__name__)
            return method(self, *args, **kwargs)
        return _decorated

    def _setdefault_entry(self, cache, key, lifespan=GENERAL_CACHE_LIFESPAN):
        """
        Returns a :class:`.CacheEntry` in the given cache with the given key if it exists.
            If it does not exist, it is efficiently created with the given lifespan.

        Similar to ``dict.setdefault``, but does not always create a :class:`.CacheEntry` object.
        """
        entry = cache.get(key)
        if not entry:
            entry = CacheEntry(lifespan, debug=self._use_debug)
            cache[key] = entry
        return entry

    def _request(self, path):
        req = urllib.request.Request(self._base + path, headers=self._headers)
        self._logger.debug("requesting %s", req.full_url)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())

    @_endpoint_method
    def providers(self, cache_bust=False):
        """:Returns: a list of provider names and their respective provider IDs."""
        return self._providers_cache.hook(cache_bust, self._request, 'Providers')

    @_endpoint_method
    def routes(self, cache_bust=False):
        """:Returns: a list of routes and their respective route IDs."""
        return self._routes_cache.hook(cache_bust, self._request, 'Routes')

    @_endpoint_method
    def directions(self, route: Union[str, int], cache_bust=False):
        """
        :param route: a |route ID|

        :Returns: the pair of directions allowed for the given route.
        """
        entry = self._setdefault_entry(self._directions_cache, self._get_cache_key(route))
        return entry.hook(cache_bust, self._request, f'Directions/{route}')

    @_endpoint_method
    def stops(
            self,
            route: Union[str, int],
            direction: Union[str, int, 'NexTrip.Directions'],
            cache_bust=False):
        """
        :param route: a |route ID|
        :param direction: a cardinal |direction| number

        :Returns: a list of stops along the route in the direction specified.
            Results include the stop name and 4 character stop code.
        """
        entry = self._setdefault_entry(self._stops_cache, self._get_cache_key(route, direction))
        return entry.hook(cache_bust, self._request, f'Stops/{route}/{direction}')

    @_endpoint_method
    def departures(self, stop_id: int, cache_bust=False):
        """
        :param stop_id: a |stop ID|.

        :Returns: a list of departures scheduled for the given |stop ID|.
        """
        entry = self._setdefault_entry(
            self._departures_cache, self._get_cache_key(stop_id),
            lifespan=DEPARTURES_CACHE_LIFESPAN)
        return entry.hook(cache_bust, self._request, f'Departures/{stop_id}')

    @_endpoint_method
    def timepoint_departures(
            self,
            route: Union[str, int],
            direction: Union[str, int, 'NexTrip.Directions'],
            stop: str,
            cache_bust=False):
        """
        :param route: a |route ID|
        :param direction: a cardinal |direction| number
        :param stop: a 4 character stop code

        :Returns: a list of departures from the given arguments.
        """
        entry = self._setdefault_entry(
            self._timepoint_departures_cache, self._get_cache_key(route, direction, stop),
            lifespan=DEPARTURES_CACHE_LIFESPAN)
        return entry.hook(cache_bust, self._request, f'{route}/{direction}/{stop}')

    @_endpoint_method
    def vehicle_locations(self, route: Union[str, int]):
        """
        :param route: a |route ID|

        :Returns: the vehicles and their properties for the given route.
        """
        return self._request(f'VehicleLocations/{route}')


def demo(route_name: str, stop_name: str, direction_name: str, debug=DEBUG, session=None):
    """
    Demos the functionality of the wrapper.

    :param route_name: substring of the bus route name
    :param stop_name: substring of the bus stop name
    :param direction_name: a cardinal direction name
    :param NexTrip session: an existing NexTrip object can be provided to preserve cache entries

    :Returns: the number of minutes until the next bus at the given
        stop going in the given direction will leave.
    """
    if session:
        nt = session
    else:
        nt = NexTrip(debug=DEBUG)

    # Debug
    logger = logging.getLogger('demo')
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[Demo]: %(message)s'))
        logger.addHandler(handler)
    if debug or nt._use_debug:
        logger.setLevel(logging.DEBUG)

    # Get route
    logger.debug("getting route %s", route_name)
    routes = nt.routes()
    route = None
    for it in routes:
        if route_name in it['Description']:
            route = it['Route']
            break
    if not route:
        raise Exception("Route not found")
    logger.debug("found route %s", route)

    # Convert direction
    logger.debug("getting direction %s", direction_name)
    direction = {
        'south': NexTrip.Directions.SOUTH,
        'east': NexTrip.Directions.EAST,
        'west': NexTrip.Directions.WEST,
        'north': NexTrip.Directions.NORTH
    }.get(direction_name)
    if not direction:
        raise Exception("Invalid direction")
    logger.debug("found direction %s", direction)

    # Get stop code
    logger.debug("getting stop %s", stop_name)
    stops = nt.stops(route, direction)
    stop = None
    for it in stops:
        if stop_name in it['Text']:
            stop = it['Value']
            break
    if not stop:
        raise Exception("Stop not found")
    logger.debug("found stop %s", stop)

    # Get departures
    logger.debug("getting departures")
    departures = nt.timepoint_departures(route, direction, stop)
    if not departures:
        return None
    logger.debug("found departures")

    # Get latest departure and the time until the bus leaves
    logger.debug("getting departure time")
    raw_time = departures[0]['DepartureTime']
    logger.debug("parsing time %s", raw_time)
    seconds = int(raw_time[6:].split('-')[0]) / 1000
    logger.debug("time parsed to %s", seconds)
    remaining = (seconds - time.time()) / 60
    if remaining <= 0:
        return None

    # Always have one minute remaining at minimum
    return round(remaining) or 1


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        usage = (
            "Usage:\n\tpython3 nextrip.py <route name> <stop name> <direction>\n\n\t"
            "Valid direction names: north, east, south, west")
        print(usage, file=sys.stderr)
        sys.exit(2)
    try:
        result = demo(*sys.argv[1:])
    except Exception as e:
        print("Error: {}".format(e.args[0]), file=sys.stderr)
        sys.exit(1)
    if result:
        print("{} Minute{}".format(result, '' if result == 1 else 's'))
    sys.exit(0)
