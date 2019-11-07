import sys
import time
from collections import Counter
from os.path import join, dirname, abspath
import requests
import json
import unicodedata
from math import sqrt

from shapely.geometry import mapping
from shapely.ops import polygonize, cascaded_union
import pandas
import shapely.wkb

from diskcache import Cache
try:
    import config
    cache = Cache(join(config.BASEDIR, 'overpass_cache'))
except ImportError:
    print("Using /tmp cache")
    cache = Cache(join('/tmp', 'overpass_cache'))

overpass_url = "http://overpass-api.de/api/interpreter"
# overpass_url = "https://overpass.kumi.systems/api/interpreter"

my_path = abspath(dirname(__file__))
with open(join(my_path, 'landmass.wkb'), 'rb') as f:
    landmass = shapely.wkb.loads(f.read())

def get_polygon(element):
    # Some polys have a gap in, just deal with one gap for now
    # Identify gaps by coords that don't have a matching pair
    members = [m for m in element['members']
               if m['type'] == 'way' and m['role'] == 'outer']
    starts = [(m['geometry'][0]['lon'], m['geometry'][0]['lat'])
              for m in members]
    ends = [(m['geometry'][-1]['lon'], m['geometry'][-1]['lat'])
            for m in members]

    c = Counter(starts + ends)
    unmatched = [point for point, count in c.items() if count == 1]
    if len(unmatched) > 2:
        raise AssertionError('More than one gap in geometry')
    extra_lines = []
    if len(unmatched) > 0:
        extra_lines.append(unmatched)

    return cascaded_union(list(
        polygonize(extra_lines + [
            [(p['lon'], p['lat']) for p in m['geometry']]
            for m in members]))).simplify(0.01).intersection(landmass)

def filter_unwanted(name):
    for unwanted in ['province', 'Province', 'district', 'District', 'division', 'Division', 'region', 'Region', 'state', 'State']:
        name = name.replace(unwanted, '')
    name = name.replace('  ', ' ')
    name = name.strip()
    return name

def admin_levels_for_point(lat, lng):
    cache_key = str(lat) + ',' + str(lng)
    try:
        result = cache[cache_key]
    except KeyError:
        query = '[out:json];is_in({}, {});relation(pivot)[boundary=administrative][admin_level~"^[3456]$"];out geom;'.format(
            lat, lng)
        sleep_time = 5
        while True:
            result = requests.get(overpass_url,
                                  params={'data': query})
            if result.status_code == 429 or result.status_code == 504:  # TOO MANY REQUESTS
                print('Too many OSM requests, sleeping for ' + str(sleep_time))
                time.sleep(sleep_time)
                sleep_time = sleep_time * 2
                continue
            result.raise_for_status()
            result = result.json()['elements']
            cache[cache_key] = result
            break
    admin_levels = {}
    for e in result:
        if 'admin_level' in e['tags']:
            polygon = get_polygon(e)
            centre = polygon.centroid
            if 'name:en' not in e['tags']:
                e['tags']['name:en'] = e['tags']['name']
            admin_levels[e['tags']['admin_level']] = {
                'id': unicodedata.normalize('NFKD', e['tags']['name:en']).encode("ascii", 'replace').replace(
                    b' ', b'_').decode('ascii') + '_' + str(e['id'])[:4], # Extra id numbers to improve chances of unique
                'name': filter_unwanted(e['tags']['name:en']),
                'local_name': e['tags']['name'],
                'latitude': centre.y,
                'longitude': centre.x,
                'geojson': json.dumps(mapping(polygon))
            }

    ret = {}
    five_used = False
    if '4' in admin_levels:
        ret['province'] = admin_levels['4']
    elif '3' in admin_levels:
        ret['province'] = admin_levels['3']
    elif '5' in admin_levels:
        ret['province'] = admin_levels['5']
        five_used = True
    else:
        raise LookupError("No admin level for " + str(lat) + ',' + str(lng))

    if '6' in admin_levels:
        ret['district'] = admin_levels['6']
    elif '5' in admin_levels and not five_used:
        ret['district'] = admin_levels['5']
    elif '4' in admin_levels and not five_used:
        ret['district'] = dict(**admin_levels['4'])
    elif '3' in admin_levels and not five_used:
        ret['district'] = dict(**admin_levels['3'])

    ret['province']['province_id'] = ret['province']['id']
    del ret['province']['id']
    ret['district']['district_id'] = ret['district']['id']
    del ret['district']['id']
    ret['district']['province_id'] = ret['province']['province_id']
    return ret['province'], ret['district']


if __name__ == '__main__':
    locations = pandas.read_csv(sys.argv[1], delimiter='\t')
    for index, row in locations.iterrows():
        print(row['location_id'], row['country_id'], row['latitude'], row['longitude'])
        a = admin_levels_for_point(row['latitude'], row['longitude'])
        print(a)
