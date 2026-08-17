import os
import xarray as xr
from datetime import datetime
from app.scripts.util import (
            open_zarr_retry,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.cdb import queryDB_json
from app.scripts.imagepng import create_imagePng

def _mean_ground_speed_kmh(species, var_time, radar_id):
    """Density-weighted mean ground speed (km/h) from the vertical profile
    nearest to var_time (within 15 minutes). None when no usable profile
    exists — the caller reports that no MTR can be derived."""
    table = 'vp_bird' if species == 'bird' else 'vp_insect'
    rows = queryDB_json(
        f"""
        SELECT COALESCE(
                   sum(t.ff * t.dens) / NULLIF(sum(t.dens), 0),
                   avg(t.ff)
               ) AS ff
        FROM {table} t
        JOIN (
            SELECT id FROM vp_polar
            WHERE radar_id = %s
              AND date_time BETWEEN %s::timestamp - interval '15 minutes'
                                AND %s::timestamp + interval '15 minutes'
            ORDER BY abs(extract(epoch FROM (date_time - %s::timestamp)))
            LIMIT 1
        ) p ON t.polar_id = p.id
        WHERE t.ff IS NOT NULL;
        """,
        (radar_id, var_time, var_time, var_time)
    )
    if not rows or rows[0]['ff'] is None:
        return None
    return float(rows[0]['ff']) * 3.6

def get_sevip_json(params):
    zarr_info = GLOBAL_CONFIG['vertical']['zarr']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, 'sevip_data', 422
            )
    ds = open_zarr_retry(zarr_path)
    time = ds.time.values
    time = time.astype('datetime64[s]')
    time = time.astype(datetime)
    format_time = '%Y-%m-%d %H:%M:%S'
    time_req = datetime.strptime(params['time'], format_time)
    it = min(range(len(time)), key=lambda i: abs(time[i] - time_req))
    ds_t = ds.isel(time=it)
    species = 1 if params['species'] == 'bird' else 0
    ds_t = ds_t.sel(species=species)

    # Derived spatial MTR: the store holds VID (#/km2); the migration
    # traffic rate across a 1 km front is VID x ground speed, with the
    # speed taken from the concurrent vertical profile (radar-domain,
    # density-weighted). MTR = vid [#/km2] x speed [km/h] -> #/km/h.
    parameter = params['parameter']
    derived_mtr = parameter == 'mtr' and 'mtr' not in ds
    read_par = 'vid' if derived_mtr else parameter

    var_time = ds_t.time.values
    var_time = var_time.astype('datetime64[s]')
    var_time = var_time.astype(datetime)
    var_time_str = var_time.strftime('%Y-%m-%d %H:%M:%S')

    values = ds_t[read_par].values
    name = ds_t[read_par].long_name
    units = ds_t[read_par].units
    if derived_mtr:
        speed_kmh = _mean_ground_speed_kmh(
            params['species'], var_time_str, params['radarID']
        )
        if speed_kmh is None:
            msg = ('No vertical-profile speed within 15 minutes of the '
                   'selected time; the MTR layer cannot be derived.')
            return response_download_error(msg, 'sevip_data', 422)
        values = values * speed_kmh
        name = 'Migration traffic rate (VID x speed)'
        units = '#/km/h'

    data = {
        'lon': ds_t.lon.values,
        'lat': ds_t.lat.values,
        'data': values
    }
    img_obj = create_imagePng(data, color_name=params['colorbar'])
    img_obj['info'] = {
                    'time': var_time_str,
                    'name': name,
                    'units': units
                }
    return response_download_json(img_obj, 'sevip_data')
