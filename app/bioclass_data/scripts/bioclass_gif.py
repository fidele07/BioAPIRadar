import os
import netCDF4 as nc
import numpy as np
from .bio_info import get_class_info
from app.scripts.util import (
        get_data_files_list,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagegif import bioclass_animeGif
import pyart

def anime_gif_bioclass(params):
    data_info = GLOBAL_CONFIG['class']
    data_files = get_data_files_list(
            data_info, params['startTime'], params['endTime']
        )
    if data_files is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'bioclass_grid_cartesian', 422
            )

    path_files = []
    for d in data_files:
        data_dir = os.path.join(data_info['dir'], d['dir'])
        for f in d['files']:
            path_files += [os.path.join(data_dir, f)]

    param_info = get_class_info(params['class'])

    frames = []
    times = []
    lon = None
    lat = None
    hgt = None

    for file_path in path_files:
        grid = pyart.io.read_grid(file_path)
        data = grid.fields[param_info['field']]['data']

        z_crds = grid.z['data']
        iz = np.argmin(np.abs(z_crds - params['height']))
        data = data[iz, :, :]

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

    frames = np.ma.array(frames)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': frames
        }
    gif_obj = bioclass_animeGif(data,
                     color_0=params['color_0'],
                     color_1=params['color_1'])

    out = {'data': gif_obj}
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
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    out['info'] = {
                    'time': times_info,
                    'height': f'{hgt} m',
                    'name': param_info['name'],
                    'class': params['class']
                }
    return response_download_json(out, 'class_data_gif')
