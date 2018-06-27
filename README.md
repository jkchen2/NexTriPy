# NexTriPy
A Python 3.6+ [NexTrip API](http://svc.metrotransit.org/) wrapper.

This wrapper provides coverage of all of the endpoints available and respects the caching requests as stated on the NexTrip API reference.

Click [here](https://jkchen2.github.io/NexTriPy/nextrip.html) for the wrapper documentation, and [here](http://svc.metrotransit.org/) for the API documentation.

## Usage
This wrapper was written to fulfill a specific demo. Given a route, stop, and direction, it will print the number of minutes remaining until the next bus leaves (or nothing if no bus is available).

Click [here](https://jkchen2.github.io/NexTriPy/demo/) for a web-based demo.

```
$ python nextrip.py "Express - Target - Hwy 252 and 73rd Av P&R - Mpls" "Target North Campus Building F" "south"
4 Minutes

$ python nextrip.py "METRO Blue Line" "Target Field Station Platform 1" "south"
57 Minutes

$ python nextrip.py "Nonexistent Route" "Target Field Station Platform 1" "south"
Error: Route not found
```

## Installation
If you have `git` installed:

`pip install --upgrade git+https://github.com/jkchen2/NexTriPy.git`

Without `git`:

`pip install --upgrade https://github.com/jkchen2/NexTriPy/tarball/master`

## Example
```py
# Create a NexTrip wrapper object
from nextrip import NexTrip
nt = NexTrip()

# METRO Blue cardinal directions
dirs = nt.directions(901)

# Get stops in the first direction provided
stops = nt.stops(901, dirs[0]['Value'])

# Print the last stop's code and name
print('{0[Value]}: {0[Text]}'.format(stops[-1]))
```

For a more extensive example, see the [wrapper documentation](https://jkchen2.github.io/NexTriPy/nextrip.html), the [demo function source](https://jkchen2.github.io/NexTriPy/_modules/nextrip.html#demo), and the [demo server source](https://github.com/jkchen2/NexTriPy/blob/server/server.py).

See the [server branch](https://github.com/jkchen2/NexTriPy/tree/server) for more information on the demo API server.
