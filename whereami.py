#!/usr/bin/env python

"""
Sanity-check locations in lat, lon or mercator forms.

Most output is on stderr, the URLs are on stdout so it's possible to use like this:
    % open `python whereami.py -13628177 4546770 -13627494 4546034`

Examples follow.

% python whereami.py 15/5241/12666
southwest:   37.76201938 -122.42064938
northeast:   37.77070423 -122.40966305
upper-left:  -13627804.35 4547084.46
lower-right: -13626581.36 4545861.47
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py 37.764897 -122.419453
mercator: -13627671.17 4546266.67
tile:     8/40/98
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py 37.764897 -122.419453 14
mercator: -13627671.17 4546266.67
tile:     14/2620/6333
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py -13627671 4546266
lat, lon: 37.76489221 -122.41945146
tile: 8/40/98
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py -13627671 4546266 12
lat, lon: 37.76489221 -122.41945146
tile: 12/655/1583
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py 37.763251 -122.424002 37.768476 -122.417865
southwest:   37.76325100 -122.42400200
northeast:   37.76847600 -122.41786500
upper-left:  -13628177.56 4546770.67
lower-right: -13627494.40 4546034.89
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py -13628177 4546770 -13627494 4546034
southwest:   37.76324465 -122.42399694
northeast:   37.76847126 -122.41786144
upper-left:  -13628177.00 4546770.00
lower-right: -13627494.00 4546034.00
http://pafciu17.dev.openstreetmap.org/?...

"""

import re
import sys
sys.path.append('ModestMaps')
import ModestMaps
import commands
from urllib import urlencode
from sys import stdout as out, stderr as err
from math import log, tan, pi, atan, pow, e

import json
import cgi

url = 'http://www.openstreetmap.org/'

def proj_command():
    """
    """
    status, path = commands.getstatusoutput('which proj')
    assert status == 0, 'Expected to get a clean exit from `which proj`'
    return path

def project(lat, lon):
    """ Project latitude, longitude to mercator x, y.
    """
    lat, lon = lat * pi/180, lon * pi/180       # degrees to radians
    x, y = lon, log(tan(0.25 * pi + 0.5 * lat)) # basic spherical mercator
    x, y = 6378137 * x, 6378137 * y             # dimensions of the earth
    
    return x, y

def unproject(x, y):
    """ Unproject mercator x, y to latitude, longitude.
    """
    x, y = x / 6378137, y / 6378137             # dimensions of the earth
    lat, lon = 2 * atan(pow(e, y)) - .5 * pi, x # basic spherical mercator
    lat, lon = lat * 180/pi, lon * 180/pi       # radians to degrees
    
    return lat, lon

def is_latlon(this, that):
    """ True if the arguments seem like a latitude, longitude
    """
    return -85 <= this and this <= 85 and -180 <= that and that <= 180

def get_tile_polygon(tile):
    """
    """
    provider = ModestMaps.OpenStreetMap.Provider()
    sw = provider.coordinateLocation(tile.down())
    ne = provider.coordinateLocation(tile.right())
    return '%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,transparency:102,thickness:3,color:0:0:0' % (sw.lon, sw.lat, sw.lon, ne.lat, ne.lon, ne.lat, ne.lon, sw.lat)

def get_point_map_url(lat, lon, zoom):
    """
    """
    q = {'mlat': lat, 'mlon': lon, 'zoom': int(zoom)}

    return url + '?' + urlencode(q)

def get_box_map_url(minlat, minlon, maxlat, maxlon):
    """
    """
    q = {'box': 'yes'}
    q['bbox'] = '%.6f,%.6f,%.6f,%.6f' % (minlon, maxlat, maxlon, minlat)

    return url + '?' + urlencode(q)

def do_latlon_point(lat, lon, zoom):
    """
    """
    provider = ModestMaps.OpenStreetMap.Provider()
    location = ModestMaps.Geo.Location(lat, lon)
    coord = provider.locationCoordinate(location).zoomTo(zoom).container()

    return {
        'mercator': '%.2f %.2f' % project(lat, lon),
        'tile': '%(zoom)d/%(column)d/%(row)d' % coord.__dict__,
        'url': get_point_map_url(lat, lon, zoom)
        }

    """
    print >> err, 'mercator: %.2f %.2f' % project(lat, lon)
    print >> err, 'in tile:  %(zoom)d/%(column)d/%(row)d' % coord.__dict__
    print >> err, ''
    print >> out, get_point_map_url(lat, lon, zoom)
    """

def do_merc_point(x, y, zoom):
    """
    """
    lat, lon = unproject(x, y)

    provider = ModestMaps.OpenStreetMap.Provider()
    location = ModestMaps.Geo.Location(lat, lon)
    coord = provider.locationCoordinate(location).zoomTo(zoom).container()

    return{
        'lat': '%.8f' % lat,
        'lon': '%.8f' % lon,
        'tile': '%(zoom)d/%(column)d/%(row)d' % coord.__dict__,
        'url': get_point_map_url(lat, lon, zoom, coord)
        }

    """
    print >> err, 'lat, lon: %.8f %.8f' % (lat, lon)
    print >> err, 'in tile:  %(zoom)d/%(column)d/%(row)d' % coord.__dict__
    print >> err, ''
    print >> out, get_point_map_url(lat, lon, zoom, coord)
    """

def do_latlon_box(minlat, minlon, maxlat, maxlon):
    """
    """

    return {
        'southwest': '%.8f %.8f' % (minlat, minlon),
        'northeast': '%.8f %.8f' % (maxlat, maxlon),
        'upper-left': '%.2f %.2f' % project(maxlat, minlon),
        'lower-right': '%.2f %.2f' % project(minlat, maxlon),
        'url': get_box_map_url(minlat, minlon, maxlat, maxlon)
        }

    """
    print >> err, 'southwest:   %.8f %.8f' % (minlat, minlon)
    print >> err, 'northeast:   %.8f %.8f' % (maxlat, maxlon)
    print >> err, 'upper-left:  %.2f %.2f' % project(maxlat, minlon)
    print >> err, 'lower-right: %.2f %.2f' % project(minlat, maxlon)
    print >> err, ''
    print >> out, get_box_map_url(minlat, minlon, maxlat, maxlon)
    """

def do_merc_box(xmin, ymin, xmax, ymax, include_tile=True):
    """
    """
    minlat, minlon = unproject(xmin, ymin)
    maxlat, maxlon = unproject(xmax, ymax)

    return do_latlon_box(minlat, minlon, maxlat, maxlon, include_tile)

def tile_box(row, column, zoom):
    """
    """
    provider = ModestMaps.OpenStreetMap.Provider()
    coord = ModestMaps.Core.Coordinate(row, column, zoom)
    southwest = provider.coordinateLocation(coord.down())
    northeast = provider.coordinateLocation(coord.right())
    
    return do_latlon_box(southwest.lat, southwest.lon, northeast.lat, northeast.lon, False)

def whereami(args):

    args, _args = [], args
    
    for arg in _args:
        args.extend([a for a in arg.split(',') if a])
    
    if len(args) is 1 and re.match(r'^\d+/\d+/\d+$', args[0]):
        zoom, column, row = map(int, args[0].split('/'))
        tile_box(row, column, zoom)
    
    elif len(args) in (2, 3):
        try:
            args = [float(a.rstrip(',')) for a in args]
        except ValueError:
            raise Exception, 'Two or three values are expected to be numeric: a point and optional zoom.'

        zoom = len(args) == 3 and args[2] or 8

        if is_latlon(*args[0:2]):
            lat, lon = args[0:2]
            return do_latlon_point(lat, lon, zoom)

        else:
            x, y = args[0:2]
            return do_merc_point(x, y, zoom)

    elif len(args) is 4:
        try:
            args = [float(a.rstrip(',')) for a in args]
        except ValueError:
            raise Exception, 'Four values are expected to be numeric: two points.'

        if is_latlon(*args[0:2]) and is_latlon(*args[2:4]):
            minlat, maxlat = min(args[0], args[2]), max(args[0], args[2])
            minlon, maxlon = min(args[1], args[3]), max(args[1], args[3])

            return do_latlon_box(minlat, minlon, maxlat, maxlon)

        elif is_latlon(*args[0:2]) or is_latlon(*args[2:4]):
            raise Exception, "Looks like you're mixing mercator and lat, lon?"

        else:
            xmin, xmax = min(args[0], args[2]), max(args[0], args[2])
            ymin, ymax = min(args[1], args[3]), max(args[1], args[3])
            return do_merc_box(xmin, ymin, xmax, ymax)

    else:
        raise Exception, "Sorry I'm not sure what to do with this input."

def app(environ, start_response):

    params = cgi.parse_qs(environ.get('QUERY_STRING', ''))

    args = []

    status = '200 OK'

    try:
        rsp = whereami(args)
    except Exception, e:
        status = '500 SERVER ERROR'
        rsp = {'error': e }

    rsp = json.dumps(rsp)

    start_response(status, [
            ("Content-Type", "text/javascript"),
            ("Content-Length", str(len(rsp)))
            ])

    return iter([rsp])

if __name__ == '__main__':

    args = sys.argv[1:]

    try:
        rsp = whereami(args)
    except Exception, e:
        print e
        sys.exit()

    for k,v in rsp.items():
        print "%s: %s" % (k, v)

    sys.exit()

