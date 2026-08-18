import os
import numpy as np
import zarr

from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import (
        decode_fill_value,
        zarr_nearest_time,
        response_download_json,
        response_download_error
    )


def _open_store(config_key, radar_id):
    zarr_info = GLOBAL_CONFIG[config_key]
    if config_key == 'vertical':
        zarr_info = zarr_info['zarr']
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_info['file'] % (radar_id)
    )
    if not os.path.exists(zarr_path):
        return None
    return zarr.open_group(zarr_path, mode='r')


def _nearest_index(coords, value):
    """Index of the grid coordinate nearest value; None outside the grid
    (beyond half a cell past either edge)."""
    coords = np.asarray(coords, dtype='float64')
    idx = int(np.abs(coords - value).argmin())
    step = float(np.abs(np.diff(coords)).mean()) if coords.size > 1 else 0.0
    if abs(float(coords[idx]) - value) > max(step, 1e-9):
        return None
    return idx


def _masked(value, fill):
    v = float(value)
    if fill is not None and v == fill:
        return None
    if np.isnan(v):
        return None
    return v


def _cell(arr, index, fill):
    """One cell (or one column when a slice is in the index), fill→NaN."""
    data = np.asarray(arr[index], dtype='float64')
    if fill is not None:
        data[data == fill] = np.nan
    return data


def get_point_value_json(params):
    """Value under the cursor for the map layers (hover readout).

    Direct zarr single-cell reads — cheap enough for debounced mousemove.
    products: 'sevip' (vid/vir/mtr by species; mtr derived as VID x
    profile speed like get_sevip), 'rgrid' (grid fields at a height or
    the column composite), 'bioclass' (class at a height or composite,
    returned as the category name).
    """
    product = params.get('product')
    lat = float(params['lat'])
    lon = float(params['lon'])
    radar_id = params['radarID']

    if product == 'sevip':
        store = _open_store('vertical', radar_id)
    elif product == 'rgrid':
        store = _open_store('grid', radar_id)
    elif product == 'bioclass':
        store = _open_store('class', radar_id)
    else:
        return response_download_error(
                f'Unknown product <{product}>.', 'point_value', 422
            )
    if store is None:
        return response_download_error(
                'Zarr data not found.', 'point_value', 422
            )

    it, time_out = zarr_nearest_time(store, params['time'])
    # grid/class stores keep lat/lon as 2D meshes (regular grid from
    # meshgrid: lat varies along axis 0, lon along axis 1); the vertical
    # store keeps 1D vectors
    lat_arr = np.asarray(store['lat'][:], dtype='float64')
    lon_arr = np.asarray(store['lon'][:], dtype='float64')
    lat_vec = lat_arr[:, 0] if lat_arr.ndim == 2 else lat_arr
    lon_vec = lon_arr[0, :] if lon_arr.ndim == 2 else lon_arr
    iy = _nearest_index(lat_vec, lat)
    ix = _nearest_index(lon_vec, lon)
    out = {'time': time_out, 'value': None, 'units': '', 'name': ''}
    if iy is None or ix is None:
        return response_download_json(out, 'point_value')

    if product == 'sevip':
        from app.biorad_data.scripts.sevip import _mean_ground_speed_kmh
        parameter = params['parameter']
        species_value = 1 if params['species'] == 'bird' else 0
        sp_idx = np.where(store['species'][:] == species_value)[0]
        isp = int(sp_idx[0]) if sp_idx.size else 0
        derived_mtr = parameter == 'mtr' and 'mtr' not in store
        read_par = 'vid' if derived_mtr else parameter
        if read_par not in store:
            return response_download_error(
                    f'Unknown parameter <{read_par}>.', 'point_value', 422
                )
        arr = store[read_par]
        fill = decode_fill_value(dict(arr.attrs))
        value = _masked(arr[isp, it, iy, ix], fill)
        attrs = dict(arr.attrs)
        name = str(attrs.get('long_name', read_par))
        units = str(attrs.get('units', ''))
        if derived_mtr and value is not None:
            speed = _mean_ground_speed_kmh(
                params['species'], time_out, radar_id
            )
            if speed is None:
                value = None
            else:
                value = value * speed
            name = 'Migration traffic rate'
            units = '#/km/h'
        out.update({'value': value, 'units': units, 'name': name})

    elif product == 'rgrid':
        from app.radar_data.scripts.rinfo import get_field_info
        info = get_field_info(params['parameter'])
        composite = float(params.get('height', -1)) < 0
        heights = store['z'][:]
        iz = (None if composite else
              int(np.abs(heights - float(params['height'])).argmin()))

        def read(field):
            arr = store[field]
            fill = decode_fill_value(dict(arr.attrs))
            if composite:
                return _cell(arr, (it, slice(None), iy, ix), fill)
            return _cell(arr, (it, iz, iy, ix), fill)

        if params['parameter'] == 'dr':
            zdr = read(get_field_info('zdr')['field'])
            rho = read(get_field_info('rho')['field'])
            zdr_lin = 10.0 ** (zdr / 10.0)
            num = 1 + zdr_lin - 2 * (zdr_lin**0.5) * rho
            den = 1 + zdr_lin + 2 * (zdr_lin**0.5) * rho
            with np.errstate(invalid='ignore', divide='ignore'):
                data = 10 * np.log10(num / den)
        else:
            data = read(info['field'])
        if composite:
            with np.errstate(invalid='ignore'):
                data = np.nanmax(data) if not np.all(np.isnan(data)) else np.nan
        v = float(data)
        out.update({
            'value': None if np.isnan(v) else v,
            'units': info['units'],
            'name': info['name'],
        })

    else:  # bioclass
        from app.bioclass_data.scripts.bio_info import get_class_info
        info = get_class_info(params['class'])
        arr = store[info['field']]
        fill = decode_fill_value(dict(arr.attrs))
        composite = float(params.get('height', -1)) < 0
        if composite:
            col = _cell(arr, (it, slice(None), iy, ix), fill)
            with np.errstate(invalid='ignore'):
                v = np.nanmax(col) if not np.all(np.isnan(col)) else np.nan
        else:
            heights = store['z'][:]
            iz = int(np.abs(heights - float(params['height'])).argmin())
            cell = _masked(arr[it, iz, iy, ix], fill)
            v = np.nan if cell is None else cell
        if np.isnan(v):
            value, category = None, None
        else:
            value = float(v)
            category = info['class_1'] if value > 0.5 else info['class_0']
        out.update({
            'value': value,
            'category': category,
            'units': '',
            'name': info['name'],
        })

    return response_download_json(out, 'point_value')
