from .config import *
from .utils import *

import yaml
import csv
import zipfile
import pymysql
import urllib.request
import osmnx as ox
from os import path, mkdir, listdir


def write_credentials(username, password):
    with open("credentials.yaml", "w") as file:
        credentials_dict = {'username': username,
                            'password': password}
        yaml.dump(credentials_dict, file)


def get_credentials():
    with open("credentials.yaml") as file:
        credentials = yaml.safe_load(file)
    return credentials["username"], credentials["password"]


def create_directories():
    directories = ('tables', 'datasets', 'maps', 'graphs')

    for directory in directories:
        if not path.exists(directory):
            mkdir(directory)
    print("Created directories\n")


def create_connection():
    conn = None
    credentials = get_credentials()
    try:
        conn = pymysql.connect(user=credentials[0],
                               password=credentials[1],
                               host=config['database_url'],
                               port=config['port'],
                               local_infile=1)
        return conn
    except Exception as e:
        print(f"Error connecting to the MariaDB Server: {e}")


def initialize_database():
    with create_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";""")
            cur.execute(f"""SET time_zone = "+00:00";""")
            cur.execute(f"""CREATE DATABASE IF NOT EXISTS property_prices DEFAULT 
            CHARACTER SET utf8 COLLATE utf8_bin;""")
            cur.execute(f"""USE property_prices""")
            conn.commit()

            print("Initialised database\n")

            # Price Paid Data
            cur.execute(f"""DROP TABLE IF EXISTS pp_data""")
            conn.commit()
            cur.execute(f"""CREATE TABLE IF NOT EXISTS pp_data (
                              `transaction_unique_identifier` tinytext COLLATE utf8_bin NOT NULL,
                              `price` int(10) unsigned NOT NULL,
                              `date_of_transfer` date NOT NULL,
                              `postcode` varchar(8) COLLATE utf8_bin NOT NULL,
                              `property_type` varchar(1) COLLATE utf8_bin NOT NULL,
                              `new_build_flag` varchar(1) COLLATE utf8_bin NOT NULL,
                              `tenure_type` varchar(1) COLLATE utf8_bin NOT NULL,
                              `primary_addressable_object_name` tinytext COLLATE utf8_bin NOT NULL,
                              `secondary_addressable_object_name` tinytext COLLATE utf8_bin NOT NULL,
                              `street` tinytext COLLATE utf8_bin NOT NULL,
                              `locality` tinytext COLLATE utf8_bin NOT NULL,
                              `town_city` tinytext COLLATE utf8_bin NOT NULL,
                              `district` tinytext COLLATE utf8_bin NOT NULL,
                              `county` tinytext COLLATE utf8_bin NOT NULL,
                              `ppd_category_type` varchar(2) COLLATE utf8_bin NOT NULL,
                              `record_status` varchar(2) COLLATE utf8_bin NOT NULL,
                              `db_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY
                            )DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1;""")
            conn.commit()

            print("Initialised price paid data table\n")

            # Postcode Data
            cur.execute(f"""DROP TABLE IF EXISTS postcode_data""")
            conn.commit()
            cur.execute(f"""CREATE TABLE IF NOT EXISTS postcode_data (
                              `postcode` varchar(8) COLLATE utf8_bin NOT NULL,
                              `status` enum('live','terminated') NOT NULL,
                              `usertype` enum('small', 'large') NOT NULL,
                              `easting` int unsigned,
                              `northing` int unsigned,
                              `positional_quality_indicator` int NOT NULL,
                              `country` enum('England', 'Wales', 'Scotland', 'Northern Ireland', 'Channel Islands', 'Isle of Man') NOT NULL,
                              `latitude` decimal(11,8) NOT NULL,
                              `longitude` decimal(10,8) NOT NULL,
                              `postcode_no_space` tinytext COLLATE utf8_bin NOT NULL,
                              `postcode_fixed_width_seven` varchar(7) COLLATE utf8_bin NOT NULL,
                              `postcode_fixed_width_eight` varchar(8) COLLATE utf8_bin NOT NULL,
                              `postcode_area` varchar(2) COLLATE utf8_bin NOT NULL,
                              `postcode_district` varchar(4) COLLATE utf8_bin NOT NULL,
                              `postcode_sector` varchar(6) COLLATE utf8_bin NOT NULL,
                              `outcode` varchar(4) COLLATE utf8_bin NOT NULL,
                              `incode` varchar(3)  COLLATE utf8_bin NOT NULL,
                              `db_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY
                            ) DEFAULT CHARSET=utf8 COLLATE=utf8_bin;""")
            conn.commit()

            print("Initialised postcode data table\n")


def upload_price_paid_data(year=1995):
    while True:
        filename = str(year) + ".csv"
        file_path = path.join(datasets, filename)
        url = config['price_paid_data_url_prefix'] + filename
        if not path.exists(file_path):
            try:
                urllib.request.urlretrieve(url, file_path)
            except Exception as _:
                break
            print(filename + " is downloaded.\n")
        else:
            print(filename + " has already been downloaded.\n")

        with create_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""USE property_prices""")
                cur.execute(f"""LOAD DATA LOCAL INFILE '{file_path}'
                                INTO TABLE pp_data FIELDS TERMINATED BY ',' ENCLOSED BY '"'
                                LINES STARTING BY '' TERMINATED BY '\n'""")
                conn.commit()

        year += 1
    print("Uploaded all available price paid data\n")


def upload_postcode_data():
    postcode_file_path = path.join(datasets, 'open_postcode_geo.csv')
    postcode_zip_path = 'open_postcode_geo.csv.zip'

    if not path.exists(postcode_file_path):
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(config['postcode_data_url'], postcode_zip_path)

    with zipfile.ZipFile(postcode_zip_path, 'r') as zip_ref:
        zip_ref.extract('open_postcode_geo.csv', datasets)
    os.remove(postcode_zip_path)

    with create_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""USE property_prices""")
            cur.execute(f"""LOAD DATA LOCAL INFILE '{postcode_file_path}' INTO TABLE postcode_data
                            FIELDS TERMINATED BY ',' 
                            LINES STARTING BY '' TERMINATED BY '\n';""")
            conn.commit()
    print("Uploaded postcode data\n")


def prices_coordinates_data(area_type='town_city', area_name='CAMBRIDGE', outcode=None, latitude=None,
                            longitude=None, boxsize='0.1',
                            start_date='2013-01-01', end_date=str(this_year) + '-12-31'):
    print('Retrieving property data... this may take a while if not cached locally...\n')


    if latitude is not None and longitude is not None:
        two = Decimal(2)
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)
        boxsize = Decimal(boxsize)
        lat_min = latitude - boxsize / two
        lat_max = latitude + boxsize / two
        lon_min = longitude - boxsize / two
        lon_max = longitude + boxsize / two
        pp_condition = ""
        pc_condition = f"""
        WHERE latitude >= {lat_min} AND
        latitude < {lat_max} AND
        longitude >= {lon_min} AND
        longitude < {lon_max}
        """
        filename = get_filename(latitude=latitude, longitude=longitude, boxsize=boxsize,
                                start_date=start_date, end_date=end_date)

        def tp(x):
            if not (x[0] == 'coordinate_box_size'):
                return False
            lat = Decimal(x[1])
            lon = Decimal(x[2])
            bs = Decimal(x[3])
            lat_min_x = lat - bs / two
            lat_max_x = lat + bs / two
            lon_min_x = lon - bs / two
            lon_max_x = lon + bs / two
            return (lat_min_x < lat_min or isclose(lat_min_x, lat_min)) and \
                   (lon_min_x < lon_min or isclose(lon_min_x, lon_min)) and \
                   (lat_max_x > lat_max or isclose(lat_max_x, lat_max)) and \
                   (lon_max_x > lon_max or isclose(lon_max_x, lon_max))

        type_predicate = tp
    elif outcode is not None:
        pp_condition = ""
        pc_condition = f"WHERE outcode = '{outcode}'"
        filename = get_filename(outcode=outcode, start_date=start_date, end_date=end_date)
        type_predicate = (lambda x: x[0] == 'outcode' and x[1] == outcode)
    else:
        pp_condition = f"{area_type} = '{area_name}' AND"
        pc_condition = ""
        filename = get_filename(area_type=area_type, area_name=area_name, start_date=start_date, end_date=end_date)
        type_predicate = (lambda x: x[0] == area_type and x[1] == area_name)

    filename = filename + '.csv'
    date_predicate = (lambda x: comp_date(x[-3], start_date) and comp_date(end_date, x[-2]))

    for fn in listdir(tables):
        parts = fn.split('#')
        if type_predicate(parts) and date_predicate(parts):
            return path.join(tables, fn), True

    with create_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""USE property_prices""")
            cur.execute(f"""SELECT pp.price, pp.date_of_transfer, pp.postcode, pp.property_type,
                            pp.new_build_flag, pp.tenure_type, pp.locality, pp.town_city, pp.district,
                            pp.county, pc.country, pc.latitude, pc.longitude
                            FROM
                            (SELECT DISTINCT price, date_of_transfer, postcode, property_type, new_build_flag, tenure_type, locality,
                            town_city, district, county
                            FROM pp_data WHERE {pp_condition}
                            date_of_transfer >= '{start_date}' AND
                            date_of_transfer <= '{end_date}') pp
                            INNER JOIN
                            (SELECT postcode, country, latitude, longitude FROM postcode_data {pc_condition}) pc
                            ON pp.postcode = pc.postcode""")
            rows = cur.fetchall()

            with open(path.join(tables, filename), 'w', newline='') as file:
                writer = csv.writer(file, delimiter=',', doublequote=False, lineterminator='\n',
                                    quoting=csv.QUOTE_MINIMAL)
                for row in rows:
                    writer.writerow(row)
            return rows, False


def road_data(north, south, east, west, network_type, custom_filter):
    _, edges = ox.graph_to_gdfs(ox.graph_from_bbox(north, south, east, west,
                                                   network_type=network_type,
                                                   truncate_by_edge=True,
                                                   custom_filter=custom_filter))
    return edges


def pois_data(north, south, east, west, tags):
    tag_gdfs = []
    for tag in tags:
        tag_gdf = ox.geometries_from_bbox(north, south, east, west, tag[1])
        tag_gdf['display name'] = tag[0]
        tag_gdfs.append(tag_gdf)
    return tag_gdfs


def init():
    create_directories()
    initialize_database()
    upload_price_paid_data()
    upload_postcode_data()
    print('Finished initialisation\n')
