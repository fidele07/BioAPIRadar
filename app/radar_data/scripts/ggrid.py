import os
import netCDF4 as nc
import numpy as np
from .rinfo import get_field_info
from app.scripts.util import (
        get_data_files_list,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagegif import create_animeGif
import pyart

def anime_gif_grid(params):
    data_info = GLOBAL_CONFIG['radar']['grid']
    data_files = get_data_files_list(
            data_info, params['startTime'], params['endTime']
        )
    if data_files is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'grid_cartesian', 422
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
    hgt = None

    for file_path in path_files:
        grid = pyart.io.read_grid(file_path)
        if params['parameter'] == 'dr':
            zdr = grid.fields['ZDR']['data']
            rho = grid.fields['RHOHV']['data']
            num = 1 + zdr - 2 * (zdr**0.5) * rho
            den = 1 + zdr + 2 * (zdr**0.5) * rho
            data = 10 * np.log10(num / den)
        else:
            data = grid.fields[param_info['field']]['data']

        z_crds = grid.z['data']
        iz = np.argmin(np.abs(z_crds - params['height']))
        data = data[iz, :, :]
        ## fill array
        # data = data.filled(np.nan)

        if hgt is None:
            hgt = z_crds[iz]

        if lon is None:
            lon, lat = grid.get_point_longitude_latitude()

        time = nc.num2date(
                    grid.time['data'][-1],
                    units=grid.time['units'],
                    calendar=grid.time['calendar']
                )
        time = cftime2datetime(time)

        frames.append(data)
        times.append(time)

    ## filled array
    # frames = np.array(frames)
    frames = np.ma.array(frames)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': frames
        }
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {
                    'time': times_info,
                    'height': f'{hgt} m',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(gif_obj, 'grid_data_gif')
