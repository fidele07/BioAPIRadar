import os
import numpy as np
from app.scripts.netcdf import read_netcdf_nc
from app.scripts.util import (
        get_data_files_list,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagegif import create_animeGif

def anime_gif_sevip(params):
    data_info = GLOBAL_CONFIG['vertical']['sevip']
    data_files = get_data_files_list(
            data_info, params['startTime'], params['endTime']
        )
    if data_files is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'sp_vertically_integrated_gif', 422
            )
    path_files = []
    for d in data_files:
        data_dir = os.path.join(data_info['dir'], d['dir'])
        for f in d['files']:
            path_files += [os.path.join(data_dir, f)]

    frames = []
    times = []
    lon = None
    lat = None
    name = None
    units = None

    for file_path in path_files:
        ncdata = read_netcdf_nc(
                    file_path, params['parameter'],
                    GLOBAL_CONFIG['vertical']['sevip']
                )
        if lon is None:
            lon = ncdata['lon']
            lat = ncdata['lat']
            name = ncdata['name']
            units = ncdata['units']

        frames.append(
                np.squeeze(ncdata['data'])
            )
        times.append(ncdata['time'])

    frames = np.ma.array(frames)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': frames
        }
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {'time': times_info, 'name': name, 'units': units}
    return response_download_json(gif_obj, 'sevip_data_gif')
