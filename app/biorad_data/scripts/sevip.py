import os
import numpy as np
import zarr
from app.scripts.util import (
        decode_fill_value,
        zarr_nearest_time,
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
    # direct zarr read — one (species, time) frame only; the xarray path
    # built dask graphs over the store's ~19M chunks per request
    store = zarr.open_group(zarr_path, mode='r')
    it, var_time_str = zarr_nearest_time(store, params['time'])
    species_value = 1 if params['species'] == 'bird' else 0
    sp_idx = np.where(store['species'][:] == species_value)[0]
    isp = int(sp_idx[0]) if sp_idx.size else 0

    # Derived spatial MTR: the store holds VID (#/km2); the migration
    # traffic rate across a 1 km front is VID x ground speed, with the
    # speed taken from the concurrent vertical profile (radar-domain,
    # density-weighted). MTR = vid [#/km2] x speed [km/h] -> #/km/h.
    parameter = params['parameter']
    derived_mtr = parameter == 'mtr' and 'mtr' not in store
    read_par = 'vid' if derived_mtr else parameter
    if read_par not in store:
        msg = f'Unknown parameter <{read_par}>.'
        return response_download_error(msg, 'sevip_data', 422)

    arr = store[read_par]
    values = np.asarray(arr[isp, it], dtype='float64')
    fill = decode_fill_value(dict(arr.attrs))
    if fill is not None:
        values[values == fill] = np.nan
    attrs = dict(arr.attrs)
    name = str(attrs.get('long_name', read_par))
    units = str(attrs.get('units', ''))
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
        'lon': store['lon'][:],
        'lat': store['lat'][:],
        'data': values
    }
    img_obj = create_imagePng(data, color_name=params['colorbar'])
    img_obj['info'] = {
                    'time': var_time_str,
                    'name': name,
                    'units': units
                }
    return response_download_json(img_obj, 'sevip_data')
