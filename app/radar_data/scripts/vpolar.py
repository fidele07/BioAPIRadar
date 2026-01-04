import os
import numpy as np
from datetime import datetime
from .rinfo import get_field_info
from app.scripts.util import (
        get_data_file_path,
        response_download_json,
        response_download_error,
        response_download_image
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.vcross import (
        compute_vcross_polar,
        vcross_format_params
    )
from app.scripts.imagepng import vcross_imagePng

### polar_0
from BioModRadar import read_radar_data

### polar_1
from BioModRadar import read_xradar_data
from .rinfo import (
        get_sweeps_fixed_angles,
        get_dtree_lat_lon_alt
    )

def vcross_section_polar_0(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_polar'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    out = _vcross_section_polar_0(pars['params'])
    if out is None:
        msg = 'No data found.'
        return response_download_error(
                msg, file, 422
            )
    return response_download_json(out, file)

def vcross_section_polar_1(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_polar'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    out = _vcross_section_polar_1(pars['params'])
    if out is None:
        msg = 'No data found.'
        return response_download_error(
                msg, file, 422
            )
    return response_download_json(out, file)

def image_vcross_section_polar_0(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_polar'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    vcross = _vcross_section_polar_0(pars['params'])
    if vcross is None:
        msg = 'No data found.'
        return response_download_error(
                msg, file, 422
            )
    img_png = vcross_imagePng(
        vcross, color_name=params['colorbar']
    )
    return response_download_image(
                img_png, file, 'png'
            )

def image_vcross_section_polar_1(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_polar'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    vcross = _vcross_section_polar_1(pars['params'])
    if vcross is None:
        msg = 'No data found.'
        return response_download_error(
                msg, file, 422
            )
    img_png = vcross_imagePng(
        vcross, color_name=params['colorbar']
    )
    return response_download_image(
                img_png, file, 'png'
            )

def _vcross_section_polar_0(params):
    polar_id = f'polar_{params['radarID']}'
    polar_info = GLOBAL_CONFIG['radar'][polar_id]
    file_path = get_data_file_path(polar_info, params['time'])
    if file_path is None:
        return None
    radar = read_radar_data(
        file_path,
        volume_type=polar_info['format_vol']
    )

    param_info = get_field_info(params['parameter'])

    time = radar.time['units'].split(' ')[-1]
    time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    time = time.strftime('%Y-%m-%d %H:%M:%S')

    if params['parameter'] == 'dr':
        zdr = radar.fields['ZDR']['data']
        rho = radar.fields['RHOHV']['data']
        num = 1 + zdr - 2 * (zdr**0.5) * rho
        den = 1 + zdr + 2 * (zdr**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = radar.fields[param_info['field']]['data']

    data = data.filled(np.nan)
    radar_alt = radar.altitude['data']
    sweeps = radar.sweep_number['data']
    lon = []
    lat = []
    alt = []
    for s in sweeps:
        slat, slon, salt = radar.get_gate_lat_lon_alt(s)
        lon += [slon]
        lat += [slat]
        alt += [salt - radar_alt]
    lon = np.vstack(lon)
    lat = np.vstack(lat)
    alt = np.vstack(alt)

    out = compute_vcross_polar(
        params, data, lon, lat, alt
    )
    out['info'] = {
        'time': time,
        'name': param_info['name'],
        'units': param_info['units'],
        'type': params['type']
    }
    return out

def _vcross_section_polar_1(params):
    polar_id = f'polar_{params['radarID']}'
    polar_info = GLOBAL_CONFIG['radar'][polar_id]
    file_path = get_data_file_path(polar_info, params['time'])
    if file_path is None:
        return None
    dtree = read_xradar_data(
            file_path,
            volume_type=polar_info['format_vol']
        )
    dtree = dtree.xradar.georeference()
    sweeps, fixed_angles = get_sweeps_fixed_angles(dtree)
    param_info = get_field_info(params['parameter'])
    radar_alt = dtree.altitude.values.item()

    time = dtree.time_coverage_start.values.item()
    time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    time = time.strftime('%Y-%m-%d %H:%M:%S')

    lon = []
    lat = []
    alt = []
    data = []
    for s in sweeps:
        ds = dtree[s]
        if params['parameter'] == 'dr':
            zdr_info = get_field_info('zdr')
            zdr = ds[zdr_info['field']].values
            zdr[zdr == zdr.min()] = np.nan
            rho_info = get_field_info('rho')
            rho = ds[rho_info['field']].values
            rho[rho == rho.min()] = np.nan
            num = 1 + zdr - 2 * (zdr**0.5) * rho
            den = 1 + zdr + 2 * (zdr**0.5) * rho
            tmp = 10 * np.log10(num / den)
        else:
            tmp = ds[param_info['field']].values
            tmp[tmp == tmp.min()] = np.nan
        data += [tmp]

        slat, slon, salt = get_dtree_lat_lon_alt(ds)
        lon += [slon]
        lat += [slat]
        alt += [salt - radar_alt]

    data = np.vstack(data)
    lon = np.vstack(lon)
    lat = np.vstack(lat)
    alt = np.vstack(alt)

    out = compute_vcross_polar(
        params, data, lon, lat, alt
    )
    out['info'] = {
        'time': time,
        'name': param_info['name'],
        'units': param_info['units'],
        'type': params['type']
    }
    return out
