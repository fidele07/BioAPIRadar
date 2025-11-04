import os
import geopandas as gpd
from ._global import GLOBAL_CONFIG
from .util import (
        response_download_json,
        response_download_error
    )

def get_map_geojson(params):
    gpd_data = get_geojson_data(params)
    if gpd_data['status'] == -1:
        return response_download_error(
                 gpd_data['message'], 'geojson_file', 422
            )
    gpd_data = gpd_data['data'].to_crs('EPSG:4326')
    gpd_data = gpd_data.to_json()
    return response_download_json(gpd_data, 'geojson_data')

def get_attr_geojson(params):
    gpd_data = get_geojson_data(params)
    if gpd_data['status'] == -1:
        return response_download_error(
                 gpd_data['message'], 'geojson_file', 422
            )
    gdf = gpd_data['data'].drop(columns=['geometry'])
    obj = gdf.to_dict(orient='records')
    return response_download_json(obj, 'geojson_attr_list')

def get_geojson_data(params):
    geojs = GLOBAL_CONFIG['geojson']
    geo_type = geojs[params['type']]
    geo_info = geo_type['json'][params['json']]
    geo_path = os.path.join(
            geojs['dir'], geo_type['dir'], geo_info['file']
        )
    if not os.path.exists(geo_path):
        msg = f'File {geo_path} not found.'
        return {'status': -1, 'message': msg}

    gpd_data = gpd.read_file(geo_path)
    keep = [geo_info['attr_id'], geo_info['attr_name'], 'geometry']
    exclude = [n for n in gpd_data.columns if not n in keep]
    gpd_data = gpd_data.drop(exclude, axis=1)
    colname = {
            geo_info['attr_id']: 'id',
            geo_info['attr_name']: 'name'
        }
    gpd_data = gpd_data.rename(columns=colname)
    return {'status': 0, 'data': gpd_data}
