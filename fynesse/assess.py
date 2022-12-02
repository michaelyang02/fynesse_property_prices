from .config import *
from . import access
from .utils import *

from shapely.geometry import Point
from matplotlib import pyplot as plt
from IPython.display import display
import numpy as np
import pandas as pd
import geopandas as gpd
import ipywidgets as widgets
from os import path

figure = None
graph = None


def prices_coordinates_data(conn, area_type='town_city', area_name='CAMBRIDGE', outcode=None, latitude=None, longitude=None, boxsize='0.1',
                            start_date='2013-01-01', end_date=str(this_year)+'-12-31'):
    data, loaded_locally = access.prices_coordinates_data(conn, area_type, area_name, outcode, latitude, longitude,
                                                          boxsize, start_date, end_date)
    df = pd.DataFrame(data, columns=['price', 'date of transfer', 'postcode', 'property type', 'new build flag',
                                     'tenure type', 'locality', 'town/city', 'district', 'county', 'country',
                                     'latitude', 'longitude'])

    if loaded_locally:
        df = df.astype({"latitude": Decimal, "longitude": Decimal})
        df = df.loc[df['date of transfer'].map(lambda d: comp_date(start_date, d) and comp_date(d, end_date))]
        if latitude is not None and longitude is not None:
            half = Decimal(0.5)
            latitude = Decimal(latitude)
            longitude = Decimal(longitude)
            boxsize = Decimal(boxsize)
            df = df.loc[(df['latitude'] >= latitude - half * boxsize) & (df['latitude'] < latitude + half * boxsize) &
                        (df['longitude'] >= longitude - half * boxsize) & (df['longitude'] < longitude + half * boxsize)]

    df['property type'] = df['property type'].map(property_type_map)
    return df


def road_data(north, south, east, west, network_type, custom_filter):
    data = access.road_data(north, south, east, west, network_type, custom_filter)
    data["color"] = data["highway"].map(lambda x: x[0] if isinstance(x, list) else x).map(road_color_map).fillna("dimgray")
    return data


def pois_data(north, south, east, west, tags):
    data = access.pois_data(north, south, east, west, tags)
    pois = gpd.GeoDataFrame(pd.concat(data, ignore_index=True))
    pois['geometry'] = pois['geometry'].to_crs(3035).centroid
    pois['geometry'] = pois['geometry'].to_crs(4326)
    return pois


def view_map(df, tags, display_name, display_size=15, latitude=None, longitude=None, boxsize='0.1', lod=3):
    print('Retrieving road data...\n')

    if latitude is None or longitude is None:
        lat_min = df['latitude'].min()
        lat_max = df['latitude'].max()
        lon_min = df['longitude'].min()
        lon_max = df['longitude'].max()

        width = lon_max - lon_min
        height = lat_max - lat_min
        tenth = Decimal(0.1)

        north = lat_max + tenth * height
        south = lat_min - tenth * height
        east = lon_max + tenth * width
        west = lon_min - tenth * width
    else:
        half = Decimal(0.5)
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)
        boxsize = Decimal(boxsize)
        width = boxsize
        height = boxsize

        north = latitude + half * height
        south = latitude - half * height
        east = longitude + half * width
        west = longitude - half * width

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    scaling_factor = 0.0081 / float(width * height) * display_size * 0.25
    gdf['marker size'] = np.power(gdf['price'] / 100000, 2) * scaling_factor

    fig, ax = plt.subplots(figsize=(display_size, display_size))

    # Plot road edges
    if lod == 3:
        network_type = "all"
        custom_filter = None
    elif lod == 2:
        network_type = "drive"
        custom_filter = None
    else:
        network_type = "drive"
        custom_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link"]'
    edges = road_data(north, south, east, west, network_type=network_type, custom_filter=custom_filter)
    edges.plot(ax=ax, linewidth=1, edgecolor=edges["color"])

    ax.set_xlim([west, east])
    ax.set_ylim([south, north])
    ax.set_xlabel("longitude", fontsize=14)
    ax.set_ylabel("latitude", fontsize=14)
    ax.set_title(display_name, fontsize=18)

    gdf.plot(ax=ax, alpha=0.2, markersize=gdf['marker size'], column="property type", cmap="viridis", categorical=True,
             categories=['Detached', 'Semi-detached', 'Terraced', 'Flat/Maisonettes', 'Others'],
             legend=True, legend_kwds={'loc': 'upper right'})
    legend = ax.get_legend()

    if tags:
        print('Retrieving POIs...\n')
        pois = pois_data(north, south, east, west, tags)
        print("{number} POIs found in the surrounding area of {display_name} ({width:.1f}km x {height:.1f}km)\n".format(
              display_name=display_name, number=len(pois), width=width * degree, height=height * degree))
        pois.plot(ax=ax, markersize=np.maximum(25, 5 * scaling_factor), marker="^", column="display name",
                  cmap="rainbow", categorical=True, categories=config['poi_map'].keys(),
                  legend=True, legend_kwds={'loc': 'upper left'})
        ax.add_artist(legend)

    print('Plotting map...\n')
    ax.set_aspect('equal')
    ax.text(1, -0.04, '© Crown copyright and database right 2021, Royal Mail copyright and database right 2022, OpenStreetMap contributors', horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)
    fig.tight_layout()
    plt.close()

    display(fig)
    return fig


def view_queried_map(year_range, price_range, property_types, pois, display_name, display_size, lod,
                     area_type=None, area_name=None, outcode=None, latitude=None, longitude=None, boxsize=None):
    with create_connection() as conn:
        df = prices_coordinates_data(conn,
                                     start_date=str(year_range[0]) + "-01-01", end_date=str(year_range[1])+"-12-31",
                                     area_type=area_type, area_name=area_name, outcode=outcode,
                                     latitude=latitude, longitude=longitude, boxsize=boxsize)
    df = df.loc[(df["price"] >= price_range[0]) & (df["price"] <= price_range[1])]
    df = df.loc[df["property type"].isin(property_types)]
    if df.empty:
        raise Exception('No property price data is available for this configuration')
    return view_map(df, tags=pois, display_name=display_name, display_size=display_size, lod=lod,
                    latitude=latitude, longitude=longitude, boxsize=boxsize)


def view_interactive_map():
    display_name = widgets.Text(placeholder='Greater Cambridge Area', description='Display name:',
                                style={'description_width': 'initial'})
    display_size = widgets.IntSlider(value=15, min=10, max=50, step=1, description="Display size:",
                                     continuous_update=False)
    lod = widgets.IntSlider(value=3, min=1, max=3, step=1, description="Road LOD:", continuous_update=False)
    displays = widgets.HBox([display_name, display_size, lod])
    area_type = widgets.Select(options=['Town/City', 'District', 'County', 'Outcode', 'Coordinates & Box size'],
                               description="Area type:")
    area_name = widgets.Text(placeholder='Cambridge', description='Area name:')
    outcode = widgets.Text(placeholder='CB2', description='Outcode:', layout=widgets.Layout(width='150px'))
    latitude = widgets.Text(placeholder='52.2', description='Latitude:')
    longitude = widgets.Text(placeholder='0.13', description='Longitude:')
    boxsize = widgets.Text(placeholder='0.09', description='Box size:')
    coordinates_box_size = widgets.VBox([latitude, longitude, boxsize])
    area = widgets.HBox([area_type, area_name, outcode, coordinates_box_size])

    display(displays)
    display(area)
    outcode.disabled = True
    for w in coordinates_box_size.children:
        w.disabled = True

    def type_changed(t):
        if t['new'] == 'Coordinates & Box size':
            area_name.disabled = True
            outcode.disabled = True
            for w in coordinates_box_size.children:
                w.disabled = False
        elif t['new'] == 'Outcode':
            area_name.disabled = True
            outcode.disabled = False
            for w in coordinates_box_size.children:
                w.disabled = True
        else:
            area_name.disabled = False
            outcode.disabled = True
            for w in coordinates_box_size.children:
                w.disabled = True

    area_type.observe(type_changed, names=['value'])

    year_range = widgets.IntRangeSlider(value=[2013, this_year], min=1995, max=this_year, step=1, description="Time range:",
                                        continuous_update=False)
    price_range = widgets.IntRangeSlider(value=[500000, 2000000], min=0, max=10000000, description="Price range:",
                                         step=10000, layout=widgets.Layout(width='1000px'))
    property_types = widgets.SelectMultiple(
        value=['Detached', 'Semi-detached', 'Terraced', 'Flat/Maisonettes', 'Others'],
        options=['Detached', 'Semi-detached', 'Terraced', 'Flat/Maisonettes', 'Others'], description="Property types:",
        style={'description_width': 'initial'})
    points_of_interest = widgets.SelectMultiple(options=config['poi_map'].keys(), description="Points of interest:",
                                                style={'description_width': 'initial'},
                                                layout=widgets.Layout(width='400px'))
    select_multiples = widgets.HBox([property_types, points_of_interest], layout=widgets.Layout(grid_gap='10px'))

    display(year_range)
    display(price_range)
    display(select_multiples)

    view_button = widgets.Button(description="View")
    save_button = widgets.Button(description="Save")

    def view_clicked(_):
        output.clear_output()
        with output:
            try:
                pois = [(p, config['poi_map'][p]) for p in points_of_interest.value]
                global figure
                figure = view_queried_map(year_range.value, price_range.value, property_types.value, pois,
                                          display_name.value, display_size.value, lod.value,
                                          area_type=None if area_name.disabled else type_map[area_type.value],
                                          area_name=None if area_name.disabled else area_name.value.upper(),
                                          outcode=None if outcode.disabled else outcode.value.upper(),
                                          latitude=None if latitude.disabled else latitude.value,
                                          longitude=None if longitude.disabled else longitude.value,
                                          boxsize=None if boxsize.disabled else boxsize.value)
            except Exception as e:
                print(e)

    def save_clicked(_):
        with output:
            global figure
            if figure:
                try:
                    figure.savefig(path.join(maps, get_filename(start_date=str(year_range.value[0]) + "-01-01",
                                                                end_date=str(year_range.value[1]) + "-12-31",
                                                                area_type=None if area_name.disabled else type_map[
                                                                    area_type.value],
                                                                area_name=None if area_name.disabled else area_name.value.upper(),
                                                                outcode=None if outcode.disabled else outcode.value.upper(),
                                                                latitude=None if latitude.disabled else latitude.value,
                                                                longitude=None if longitude.disabled else longitude.value,
                                                                boxsize=None if boxsize.disabled else boxsize.value)) + ".svg")
                except Exception as e:
                    print(e)
                else:
                    print('Successfully saved map\n')
            else:
                print('Failed to save map as none is generated\n')

    view_button.on_click(view_clicked)
    save_button.on_click(save_clicked)
    buttons = widgets.HBox([view_button, save_button])

    display(buttons)
    output = widgets.Output()
    display(output)


def view_queried_graph(year_range, property_types, display_size,
                       area_type=None, area_name=None, outcode=None, latitude=None, longitude=None, boxsize=None):
    with create_connection() as conn:
        df = prices_coordinates_data(conn, start_date=str(year_range[0]) + "-01-01", end_date=str(year_range[1]) + "-12-31",
                                     area_type=area_type, area_name=area_name, outcode=outcode, latitude=latitude,
                                     longitude=longitude, boxsize=boxsize)
    df = df.loc[df["property type"].isin(property_types)]

    if df.empty:
        raise Exception('No property price data is available for this configuration')

    print('Plotting graph...\n')
    fig, ax = plt.subplots(figsize=(display_size, display_size * 0.5))

    ax.set_xlabel("year", fontsize=14)
    ax.set_ylabel("price", fontsize=14)
    ax.ticklabel_format(style='plain')
    ax.set_title("Price Percentiles by Property Types", fontsize=18)
    ax.set_xlim([year_range[0], year_range[1]])

    type_predicate = (lambda ptype: df['property type'] == ptype)
    year_predicate = (lambda year: df['date of transfer'].map(
        lambda d: comp_date(str(year) + '-01-01', d) and comp_date(d, str(year) + '-12-31')))

    type_year_data = [(ptype, [df.loc[type_predicate(ptype) & year_predicate(year)]['price'].to_numpy()
                               for year in range(year_range[0], year_range[1] + 1)]) for ptype in property_types]

    colors = plt.cm.viridis(np.linspace(0, 1, 5))
    years = range(year_range[0], year_range[1] + 1)

    for ptype, data in type_year_data:
        color = colors[property_types_list.index(ptype)]
        quantiles = np.vstack([np.quantile(year, [0.25, 0.5, 0.75]) for year in data]).transpose()
        ax.plot(years, quantiles[0], color=color, label=ptype + ' 25%',
                linestyle='-.', alpha=0.5)
        ax.plot(years, quantiles[1], color=color, label=ptype + ' 50%', marker='o')
        ax.plot(years, quantiles[2], color=color, label=ptype + ' 75%',
                linestyle='--', alpha=0.5)
        ax.fill_between(years, quantiles[0], quantiles[2], alpha=0.1, color=color)

    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.text(1, -0.12, '© Crown copyright and database right 2021, Royal Mail copyright and database right 2022',
            horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)
    fig.tight_layout()
    plt.close()

    display(fig)
    return fig


def view_interactive_graph():
    area_type = widgets.Select(options=['Town/City', 'District', 'County', 'Outcode', 'Coordinates & Box size'],
                               description="Area type:")
    area_name = widgets.Text(placeholder='Cambridge', description='Area name:')
    outcode = widgets.Text(placeholder='CB2', description='Outcode:', layout=widgets.Layout(width='150px'))
    latitude = widgets.Text(placeholder='52.2', description='Latitude:')
    longitude = widgets.Text(placeholder='0.13', description='Longitude:')
    boxsize = widgets.Text(placeholder='0.09', description='Box size:')
    coordinates_box_size = widgets.VBox([latitude, longitude, boxsize])
    area = widgets.HBox([area_type, area_name, outcode, coordinates_box_size])
    display(area)
    outcode.disabled = True
    for w in coordinates_box_size.children:
        w.disabled = True

    def type_changed(t):
        if t['new'] == 'Coordinates & Box size':
            area_name.disabled = True
            outcode.disabled = True
            for w in coordinates_box_size.children:
                w.disabled = False
        elif t['new'] == 'Outcode':
            area_name.disabled = True
            outcode.disabled = False
            for w in coordinates_box_size.children:
                w.disabled = True
        else:
            area_name.disabled = False
            outcode.disabled = True
            for w in coordinates_box_size.children:
                w.disabled = True

    area_type.observe(type_changed, names=['value'])

    year_range = widgets.IntRangeSlider(value=[2013, this_year], min=1995, max=this_year, step=1, description="Time range:",
                                        continuous_update=False)
    display_size = widgets.IntSlider(value=10, min=8, max=15, step=1, description="Display size:",
                                     continuous_update=False)
    sliders = widgets.HBox([year_range, display_size], layout=widgets.Layout(grid_gap='10px'))
    property_types = widgets.SelectMultiple(
        value=['Detached', 'Semi-detached', 'Terraced', 'Flat/Maisonettes', 'Others'],
        options=['Detached', 'Semi-detached', 'Terraced', 'Flat/Maisonettes', 'Others'], description="Property types:",
        style={'description_width': 'initial'})

    display(sliders)
    display(property_types)

    view_button = widgets.Button(description="View")
    save_button = widgets.Button(description="Save")

    def view_clicked(_):
        output.clear_output()
        with output:
            try:
                global graph
                graph = view_queried_graph(year_range.value, property_types.value, display_size.value,
                                           area_type=None if area_name.disabled else type_map[area_type.value],
                                           area_name=None if area_name.disabled else area_name.value.upper(),
                                           outcode=None if outcode.disabled else outcode.value.upper(),
                                           latitude=None if latitude.disabled else latitude.value,
                                           longitude=None if longitude.disabled else longitude.value,
                                           boxsize=None if boxsize.disabled else boxsize.value)
            except Exception as e:
                print(e)

    def save_clicked(_):
        with output:
            global graph
            if graph:
                try:
                    graph.savefig(path.join(graphs,
                                            get_filename(start_date=str(year_range.value[0]) + "-01-01",
                                                         end_date=str(year_range.value[1]) + "-12-31",
                                                         area_type=None if area_name.disabled else type_map[area_type.value],
                                                         area_name=None if area_name.disabled else area_name.value.upper(),
                                                         outcode=None if outcode.disabled else outcode.value.upper(),
                                                         latitude=None if latitude.disabled else latitude.value,
                                                         longitude=None if longitude.disabled else longitude.value,
                                                         boxsize=None if boxsize.disabled else boxsize.value)) + ".svg")
                except Exception as e:
                    print(e)
                else:
                    print('Successfully saved graph\n')
            else:
                print('Failed to save graph as none is generated\n')

    view_button.on_click(view_clicked)
    save_button.on_click(save_clicked)
    buttons = widgets.HBox([view_button, save_button])

    display(buttons)
    output = widgets.Output()
    display(output)


def labelled(latitude, longitude, boxsize, radius, predict):
    with create_connection() as conn:
        df = prices_coordinates_data(conn, latitude=latitude, longitude=longitude, boxsize=boxsize,
                                     start_date='1995-01-01', end_date=str(this_year)+'-12-31')

    normalized_day = df['date of transfer'].apply(normalize_day).to_numpy()
    ind = [np.where(df['property type'] == pt, 1, 0) for pt in property_types_list]
    ind_day = ind * normalized_day
    ind_day_2 = ind * np.square(normalized_day)
    ind_day_3 = ind * np.power(normalized_day, 3)

    half = Decimal(0.5)
    latitude = Decimal(latitude)
    longitude = Decimal(longitude)
    boxsize = Decimal(boxsize)

    north = latitude + half * boxsize + radius
    south = latitude - half * boxsize - radius
    east = longitude + half * boxsize + radius
    west = longitude - half * boxsize - radius

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    pois = [pois_data(north, south, east, west, i) for i in config['poi_map'].items()]

    number_of_pois = [gdf.apply(lambda p: count_poi(p['geometry'], poi, radius), axis=1) for poi in pois]
    distance_to_closest_pois = [gdf.apply(lambda p: dist_poi(p, poi, radius), axis=1) for poi in pois]

    (lat, lon, date, ptype) = predict
    i0 = [1 if ptype == pt else 0 for pt in property_types_list]
    i1 = i0 * normalize_day(date)
    i2 = i0 * np.square(normalize_day(date))
    i3 = i0 * np.power(normalize_day(date), 3)
    nop = [count_poi(Point(lon, lat), poi, radius) for poi in pois]
    dtcp = [dist_poi(Point(lon, lat), poi, radius) for poi in pois]

    return (np.column_stack([*ind, *ind_day, *ind_day_2, *ind_day_3, *number_of_pois, *distance_to_closest_pois]),
            df['price'].to_numpy(), np.column_stack([*i0, *i1, *i2, *i3, *nop, *dtcp]))
