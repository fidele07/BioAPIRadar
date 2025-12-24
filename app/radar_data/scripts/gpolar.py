import os
import numpy as np
from datetime import datetime
from .rinfo import get_field_info
from app.scripts.util import (
        get_data_files_list,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagegif import create_animeGif

### polar_0
from BioModRadar import read_radar_data

### polar_1
from BioModRadar import read_xradar_data
from .rinfo import (
        get_sweeps_fixed_angles,
        get_dtree_lat_lon_alt
    )

def anime_gif_polar_0(params):
    polar_id = f'polar_{params['radarID']}'
    data_info = GLOBAL_CONFIG['radar'][polar_id]
    data_files = get_data_files_list(
            data_info, params['startTime'], params['endTime']
        )
    if data_files is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'polar_volume', 422
            )
    path_files = []
    for d in data_files:
        data_dir = os.path.join(data_info['dir'], d['dir'])
        for f in d['files']:
            path_files += [os.path.join(data_dir, f)]

    param_info = get_field_info(params['parameter'])

    frames = []
    times = []
    lon = None
    lat = None
    elv = None

    for file_path in path_files:
        radar = read_radar_data(
            file_path,
            volume_type=data_info['format_vol']
        )
        fixed_angles = radar.fixed_angle['data']
        elv_angle = float(params['elevation_angle'])
        isw = np.argmin(np.abs(fixed_angles - elv_angle))
        sweep = radar.sweep_number['data'][isw]
        radar = radar.extract_sweeps([sweep])

        if params['parameter'] == 'dr':
            zdr = radar.fields['ZDR']['data']
            rho = radar.fields['RHOHV']['data']
            num = 1 + zdr - 2 * (zdr**0.5) * rho
            den = 1 + zdr + 2 * (zdr**0.5) * rho
            data = 10 * np.log10(num / den)
        else:
            data = radar.fields[param_info['field']]['data']

        data = data.filled(np.nan)

        if elv is None:
            elv = fixed_angles[isw]

        if lon is None:
            lat, lon, _ = radar.get_gate_lat_lon_alt(0)

        time = radar.time['units'].split(' ')[-1]
        time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

        frames.append(data)
        times.append(time)

    frames = np.array(frames)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': frames
        }
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {
                    'time': times_info,
                    'elevation_angle': f'{elv} deg',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(gif_obj, 'polar_data_gif')

def anime_gif_polar_1(params):
    polar_id = f'polar_{params['radarID']}'
    data_info = GLOBAL_CONFIG['radar'][polar_id]
    data_files = get_data_files_list(
            data_info, params['startTime'], params['endTime']
        )
    if data_files is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'polar_volume', 422
            )
    path_files = []
    for d in data_files:
        data_dir = os.path.join(data_info['dir'], d['dir'])
        for f in d['files']:
            path_files += [os.path.join(data_dir, f)]

    param_info = get_field_info(params['parameter'])

    frames = []
    times = []
    lon = None
    lat = None
    elv = None

    for file_path in path_files:
        dtree = read_xradar_data(
                file_path,
                volume_type=data_info['format_vol']
            )
        dtree = dtree.xradar.georeference()
        sweeps, fixed_angles = get_sweeps_fixed_angles(dtree)
        elv_angle = float(params['elevation_angle'])
        isw = np.argmin(np.abs(fixed_angles - elv_angle))
        ds = dtree[sweeps[isw]]

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

        if elv is None:
            elv = fixed_angles[isw]

        if lon is None:
            lat, lon, _ = get_dtree_lat_lon_alt(ds)

        time = dtree.time_coverage_start.values.item()
        time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

        frames.append(data)
        times.append(time)

    frames = np.array(frames)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': frames
        }
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {
                    'time': times_info,
                    'elevation_angle': f'{elv} deg',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(gif_obj, 'polar_data_gif')
