import os
import numpy as np
import xarray as xr
from datetime import datetime
from app.scripts.util import (
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagegif import create_animeGif

def anime_gif_sevip(params):
    zarr_info = GLOBAL_CONFIG['vertical']['zarr']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, 'sevip_data_gif', 422
            )
    ds = xr.open_zarr(
        zarr_path, consolidated=False
    )
    format_time = '%Y-%m-%d %H:%M:%S'
    start_time = datetime.strptime(
        params['startTime'], format_time
    )
    end_time = datetime.strptime(
        params['endTime'], format_time
    )
    try:
        ds_t = ds.sel(time=slice(start_time, end_time))
    except:
        msg = 'No data found.'
        return response_download_error(
                msg, 'sevip_data_gif', 422
            )

    species = 1 if params['species'] == 'bird' else 0
    ds_t = ds_t.sel(species=species)

    frames = []
    times = []
    lon = None
    lat = None
    name = None
    units = None

    for t in ds_t.time.values:
        if lon is None:
            lon = ds_t.lon.values
            lat = ds_t.lat.values
            name = ds_t[params['parameter']].long_name
            units = ds_t[params['parameter']].units

        fr = ds_t[params['parameter']].sel(time=t)
        frames.append(
                np.squeeze(fr.values)
            )
        times.append(t)

    frames = np.array(frames)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': frames
        }
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times = [t.astype('datetime64[s]') for t in times]
    times = [t.astype(datetime) for t in times]
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {'time': times_info, 'name': name, 'units': units}
    return response_download_json(gif_obj, 'sevip_data_gif')
