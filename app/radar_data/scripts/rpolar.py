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

def download_polar(params):
    polar_info = GLOBAL_CONFIG['radar']['polar']
    file_path = get_data_file_path(polar_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'polar_volume', 422
            )
    radar = pyart.aux_io.read_odim_h5(
            file_path, file_field_names=True, delay_field_loading=True
        )
    fixed_angles = radar.fixed_angle['data']
    elv_angle = float(params['elevation_angle'])
    isw = np.argmin(np.abs(fixed_angles - elv_angle))
    sweep = radar.sweep_number['data'][isw]
    lat, lon, _ = radar.get_gate_lat_lon_alt(sweep)
    radar = radar.extract_sweeps([sweep])
    param_info = get_field_info(params['parameter'])

    if params['parameter'] == 'dr':
        zdr = radar.fields['ZDR']['data']
        rho = radar.fields['RHOHV']['data']
        num = 1 + zdr - 2 * (zdr**0.5) * rho
        den = 1 + zdr + 2 * (zdr**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = radar.fields[param_info['field']]['data']

    data = {'lon': lon, 'lat': lat, 'data': data}
    img_obj = create_imagePng(data, color_name=params['colorbar'])

    time = nc.num2date(
                radar.time['data'][-1],
                units=radar.time['units'],
                calendar=radar.time['calendar']
            )
    time = cftime2datetime(time)

    img_obj['info'] = {
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'elevation_angle': f'{fixed_angles[isw]} deg',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(img_obj, 'polar_data')
