import datetime
from decimal import Decimal

property_type_map = {
    'D': 'Detached',
    'S': 'Semi-detached',
    'T': 'Terraced',
    'F': 'Flat/Maisonettes',
    'O': 'Others'
}

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


def comp_date(earlier, later):
    return datetime.datetime.strptime(earlier, '%Y-%m-%d') <= datetime.datetime.strptime(later, '%Y-%m-%d')


def get_filename(area_type='town_city', area_name='CAMBRIDGE', outcode=None, latitude=None, longitude=None,
                 boxsize='0.1',
                 start_date='2013-01-01', end_date='2022-12-31'):
    if latitude is not None and longitude is not None:
        return "coordinate_box_size" + "#" + str(latitude) + '#' + str(longitude) + '#' + str(
            boxsize) + '#' + start_date + '#' + end_date + '#'
    elif outcode is not None:
        return "outcode" + "#" + outcode + '#' + start_date + '#' + end_date + '#'
    else:
        return area_type + '#' + area_name.replace(" ", "_").replace("'", "_") + '#' + start_date + '#' + end_date + '#'


def isclose(x, y):
    return abs(x - y) <= Decimal('0.000001')
