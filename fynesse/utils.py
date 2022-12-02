from .config import *
import pymysql
import datetime
from decimal import Decimal

tables = 'tables'
datasets = 'datasets'
maps = 'maps'
graphs = 'graphs'

degree = Decimal(111)

day_zero = datetime.datetime(year=1995, month=1, day=1)
this_year = datetime.date.today().year

property_type_map = {
    'D': 'Detached',
    'S': 'Semi-detached',
    'T': 'Terraced',
    'F': 'Flat/Maisonettes',
    'O': 'Others'
}

property_types_list = ['Detached', 'Semi-detached', 'Terraced', 'Flat/Maisonettes', 'Others']

road_color_map = {
        "trunk": "orange",
        "motorway": "orange",
        "primary": "orange",
        "secondary": "darkgoldenrod",
        "tertiary": "darkgoldenrod",
        "trunk_link": "orange",
        "motorway_link": "orange",
        "primary_link": "orange",
        "secondary_link": "darkgoldenrod",
        "tertiary_link": "darkgoldenrod",
}

type_map = {
    'Town/City': 'town_city',
    'District': 'district',
    'County': 'county'
}

username = None
password = None


def create_connection():
    conn = None
    try:
        conn = pymysql.connect(user=username,
                               passwd=password,
                               host=config['database_url'],
                               port=config['port'],
                               local_infile=1)
    except Exception as e:
        print(f"Error connecting to the MariaDB Server: {e}")
    return conn


def normalize_day(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d') - day_zero


def comp_date(earlier, later):
    return datetime.datetime.strptime(earlier, '%Y-%m-%d') <= datetime.datetime.strptime(later, '%Y-%m-%d')


def get_filename(area_type='town_city', area_name='CAMBRIDGE', outcode=None, latitude=None, longitude=None,
                 boxsize='0.1',
                 start_date='2013-01-01', end_date=str(this_year)+'-12-31'):
    if latitude is not None and longitude is not None:
        return "coordinate_box_size" + "#" + str(latitude) + '#' + str(longitude) + '#' + str(
            boxsize) + '#' + start_date + '#' + end_date + '#'
    elif outcode is not None:
        return "outcode" + "#" + outcode + '#' + start_date + '#' + end_date + '#'
    else:
        return area_type + '#' + area_name.replace(" ", "_").replace("'", "_") + '#' + start_date + '#' + end_date + '#'


def isclose(x, y):
    return abs(x - y) <= Decimal('0.000001')


def count_poi(p, poi_df, radius):
    dists = poi_df['geometry'].distance(p['geometry'])
    return len(dists < radius)


def dist_poi(p, poi_df, radius):
    dists = poi_df['geometry'].distance(p['geometry'])
    dists = dists[dists < radius]
    if dists.empty:
        return radius
    else:
        return dists.min()
