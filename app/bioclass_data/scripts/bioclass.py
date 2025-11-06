import os
import netCDF4 as nc
import numpy as np
from app.scripts.util import (
        get_data_file_path,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import bioclass_imagePng
import pyart

def download_bioclass(params):
    class_info = GLOBAL_CONFIG['class']
    file_path = get_data_file_path(class_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'bio_grid_cartesian', 422
            )

    grid = pyart.io.read_grid(file_path)
    param_info = get_class_info(params['class'])
    data = grid.fields[param_info['field']]['data']

    lon, lat = grid.get_point_longitude_latitude()
    z_crds = grid.z['data']
    iz = np.argmin(np.abs(z_crds - params['height']))
    data = data[iz, :, :]
    data = {'lon': lon, 'lat': lat, 'data': data}
    img_obj = bioclass_imagePng(data,
                             color_0=params['color_0'],
                             color_1=params['color_1'])
    out = {'data': img_obj}
    out['legend'] = {
            'class_0': {
                'name': param_info['class_0'],
                'color': params['color_0']
            },
            'class_1': {
                'name': param_info['class_1'],
                'color': params['color_1']
            }
        }

    time = nc.num2date(
                grid.time['data'][-1],
                units=grid.time['units'],
                calendar=grid.time['calendar']
            )
    time = cftime2datetime(time)

    out['info'] = {
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'height': f'{z_crds[iz]} m',
                    'name': param_info['name'],
                    'class': params['class']
                }
    return response_download_json(out, 'class_data')

def get_class_info(field):
    radar_fields = [
            {
                'id': 'species', 'field': 'BIO_CLASS',
                'class_0': 'Insect', 'class_1': 'Bird',
                'name': 'Bird vs Insect Classification'
            },
            {
                'id': 'biometeo', 'field': 'DR_CLASS',
                'class_0': 'Meteorological', 'class_1': 'Biological',
                'name': 'Biological vs Meteorological Classification'
            }
        ]
    return [f for f in radar_fields if f['id'] == field][0]
