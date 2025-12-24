import os
import numpy as np
from datetime import datetime
from .rinfo import get_field_info
from app.scripts.util import (
        get_data_file_path,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

### polar_0
from BioModRadar import read_radar_data

### polar_1
from BioModRadar import read_xradar_data
from .rinfo import (
        get_sweeps_fixed_angles,
        get_dtree_lat_lon_alt
    )

def download_polar_0(params):
    polar_id = f'polar_{params['radarID']}'
    polar_info = GLOBAL_CONFIG['radar'][polar_id]
    file_path = get_data_file_path(polar_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'polar_volume', 422
            )
    radar = read_radar_data(
        file_path,
        volume_type=polar_info['format_vol']
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

    time = radar.time['units'].split(' ')[-1]
    time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

    img_obj['info'] = {
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'elevation_angle': f'{fixed_angles[isw]} deg',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(img_obj, 'polar_data')

def download_polar_1(params):
    polar_id = f'polar_{params['radarID']}'
    polar_info = GLOBAL_CONFIG['radar'][polar_id]
    file_path = get_data_file_path(polar_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'polar_volume', 422
            )
    dtree = read_xradar_data(
            file_path,
            volume_type=polar_info['format_vol']
        )
    dtree = dtree.xradar.georeference()
    sweeps, fixed_angles = get_sweeps_fixed_angles(dtree)
    elv_angle = float(params['elevation_angle'])
    isw = np.argmin(np.abs(fixed_angles - elv_angle))
    ds = dtree[sweeps[isw]]
    lat, lon, _ = get_dtree_lat_lon_alt(ds)
    param_info = get_field_info(params['parameter'])

    if params['parameter'] == 'dr':
        zdr_info = get_field_info('zdr')
        zdr = ds[zdr_info['field']].values
        zdr[zdr == zdr.min()] = np.nan
        rho_info = get_field_info('rho')
        rho = ds[rho_info['field']].values
        rho[rho == rho.min()] = np.nan
        num = 1 + zdr - 2 * (zdr**0.5) * rho
        den = 1 + zdr + 2 * (zdr**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = ds[param_info['field']].values
        data[data == data.min()] = np.nan

    data = {'lon': lon, 'lat': lat, 'data': data}
    img_obj = create_imagePng(data, color_name=params['colorbar'])

    time = dtree.time_coverage_start.values.item()
    time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

    img_obj['info'] = {
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'elevation_angle': f'{fixed_angles[isw]} deg',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(img_obj, 'polar_data')
