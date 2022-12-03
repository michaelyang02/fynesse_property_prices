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

table_column_list = ['price', 'date of transfer', 'postcode', 'property type', 'new build flag',
                     'tenure type', 'locality', 'town/city', 'district', 'county', 'country',
                     'latitude', 'longitude']


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


def normalize_year(date):
    return (datetime.datetime.strptime(date, '%Y-%m-%d') - day_zero).days / 365.


def comp_date(earlier, later):
    return datetime.datetime.strptime(earlier, '%Y-%m-%d') <= datetime.datetime.strptime(later, '%Y-%m-%d')


def add_days(date, days):
    return (datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=days)).strftime('%Y-%m-%d')



def isclose(x, y):
    return abs(x - y) <= Decimal('0.000001')


def count_poi(p, poi, radius):
    radius = radius * 111000
    dists = poi.distance(p)
    return len(dists < radius)


def dist_poi(p, poi, radius):
    radius = float(radius * 111000)
    dists = poi.distance(p)
    dists = dists[dists < radius]
    if dists.empty:
        dist = radius
    else:
        dist = dists.min()
    return -(1 / radius) * dist + 1
