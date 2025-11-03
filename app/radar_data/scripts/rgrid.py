import os
import netCDF4 as nc
import numpy as np
from .rinfo import get_field_info
from app.scripts.util import (
        get_data_file_path,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng
import pyart

def download_grid(params):
    grid_info = GLOBAL_CONFIG['radar']['grid']
    file_path = get_data_file_path(grid_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'grid_cartesian', 422
            )
    grid = pyart.io.read_grid(file_path)
    param_info = get_field_info(params['parameter'])
    if params['parameter'] == 'dr':
        zdr = grid.fields['ZDR']['data']
        rho = grid.fields['RHOHV']['data']
        num = 1 + zdr - 2 * (zdr**0.5) * rho
        den = 1 + zdr + 2 * (zdr**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = grid.fields[param_info['field']]['data']

    lon, lat = grid.get_point_longitude_latitude()
    z_crds = grid.z['data']
    iz = np.argmin(np.abs(z_crds - params['height']))
    data = data[iz, :, :]
    data = {'lon': lon, 'lat': lat, 'data': data}
    img_obj = create_imagePng(data, color_name=params['colorbar'])
    time = nc.num2date(
                grid.time['data'][-1],
                units=grid.time['units'],
                calendar=grid.time['calendar']
            )
    time = cftime2datetime(time)

    img_obj['info'] = {
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'height': f'{z_crds[iz]} m',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(img_obj, 'grid_data')
