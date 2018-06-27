# Server demo
To see example usage of NexTriPy, you can run this demo server.

This code runs a simple Flask server that exposes the demo function and endpoint methods:
* `/demo?route=foo&stop=bar&direction=biz` (same arguments as the [demo](https://jkchen2.github.io/NexTriPy/nextrip.html#nextrip.demo) function)
* `/providers`
* `/routes`
* `/directions/<int:route>`
* `/stops/<int:route>/<int:direction>`
* `/departures/<int:stop_id>`
* `/timepoint_departures/<int:route>/<int:direction>/<stop>`
* `/vehicle_locations/<int:route>`

Additionally, the endpoint methods can accept an optional query parameter `?cache_bust` to forcefully bypass the cache.

## Usage
The server will always run on port 8080. If you are running the script directly, be sure to change the last line if necessary. If you are running the server through Docker, always map to port 8080.

To run any of these in debug mode, simply append `debug` to the end of the command.

### Python 3.6+
`python server.py`

### Docker
`docker run -p 80:8080 -it jkchen2/ntserver`

## Building
To manually build a most up-to-date image, run the following:
```
$ mkdir ntserver && cd ntserver
$ wget -O archive.tar.gz https://github.com/jkchen2/NexTriPy/tarball/server
$ tar -xf archive.tar.gz --strip-components=1
$ docker build --no-cache -t jkchen2/ntserver .
```
