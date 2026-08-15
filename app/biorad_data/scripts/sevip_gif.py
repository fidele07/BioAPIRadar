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
        zarr_path, consolidated=True
    )
    time = [
        t.astype('datetime64[s]')
        for t in ds.time.values
    ]
    time = [t.astype(datetime) for t in time]
    format_time = '%Y-%m-%d %H:%M:%S'
    start_time = datetime.strptime(
        params['startTime'], format_time
    )
    end_time = datetime.strptime(
        params['endTime'], format_time
    )
    it = [
        i for i, t in enumerate(time)
        if start_time <= t <= end_time
    ]
    if len(it) == 0:
        msg = 'No data found.'
        return response_download_error(
                msg, 'sevip_data_gif', 422
            )
    ds_t = ds.isel(time=it)
    times = [time[i] for i in it]
    species = 1 if params['species'] == 'bird' else 0
    ds_t = ds_t.sel(species=species)

    lon = ds_t.lon.values
    lat = ds_t.lat.values
    name = ds_t[params['parameter']].long_name
    units = ds_t[params['parameter']].units
    data = ds_t[params['parameter']].values

    ix_time = list(enumerate(times))
    ix_time = sorted(ix_time, key=lambda x: x[1])
    times = [x[1] for x in ix_time]
    ix = [x[0] for x in ix_time]
    data = data[ix, :, :]
    data = np.ma.masked_invalid(data)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': data
        }
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {'time': times_info, 'name': name, 'units': units}
    return response_download_json(gif_obj, 'sevip_data_gif')
