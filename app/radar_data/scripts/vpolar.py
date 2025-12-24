import os
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from .rinfo import get_field_info
from app.scripts.util import (
        get_data_file_path,
        response_download_json,
        response_download_error,
        response_download_image
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.interp import (
        get_line_equation,
        nearest_neighbor_max_radius
    )
from app.scripts.imagepng import vcross_imagePng
from app.scripts.checkparams import *

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

    out = _compute_vcross(
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

    out = _compute_vcross(
        params, data, lon, lat, alt
    )
    out['info'] = {
                    'time': time,
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return out

def _compute_vcross(params, data, lon, lat, alt):
    mn_lo, mx_lo = np.min(lon), np.max(lon)
    mn_la, mx_la = np.min(lat), np.max(lat)
    mn_al, mx_al = np.min(alt), np.max(alt)

    hgt = np.linspace(0, 5000, 21)
    xlon = np.arange(mn_lo, mx_lo, 0.0045)
    xlat = np.arange(mn_la, mx_la, 0.0045)
    xl, yl = get_line_equation(
          xlon, xlat, params['startLon'],
          params['startLat'], params['endLon'],
          params['endLat'], params['segment']
        )
    nx = len(xl)
    nz = len(hgt)
    zl1 = np.repeat(hgt, nx)
    xl1 = np.concatenate([xl] * nz)
    yl1 = np.concatenate([yl] * nz)

    # scaling
    s_lo = (lon - mn_lo) / (mx_lo - mn_lo)
    s_la = (lat - mn_la) / (mx_la - mn_la)
    s_al = (alt - mn_al) / (mx_al - mn_al)

    s_xl = (xl1 - mn_lo) / (mx_lo - mn_lo)
    s_yl = (yl1 - mn_la) / (mx_la - mn_la)
    s_zl = (zl1 - mn_al) / (mx_al - mn_al)

    max_radius = np.sqrt(
            np.diff(s_xl[:2])**2 + np.diff(s_yl[:2])**2 + s_zl[nx]**2
        )
    points = np.array([s_lo.ravel(), s_la.ravel(), s_al.ravel()]).T
    new_points = np.vstack((s_xl, s_yl, s_zl)).T

    tmp = data.ravel()
    im = ~np.isnan(tmp)
    vcross = nearest_neighbor_max_radius(
                points[im, :], tmp[im], new_points, 2 * max_radius
            )
    vcross = vcross.reshape((nz, nx))

    dist = [0]
    for i in range(1, nx):
        p1 = (yl[i - 1], xl[i - 1])
        p2 = (yl[i], xl[i])
        dist.append(dist[-1] + geodesic(p1, p2).km)
    dist = np.array(dist)
    dist = np.round(dist, 4)

    vcross = np.round(vcross, 4)
    vcross = np.where(np.isnan(vcross), None, vcross)

    return {
        'vcross': vcross.tolist(),
        'xaxis': {
                'values': dist.tolist(),
                'label': 'Distance along transect (km)'
            },
        'yaxis': {
                'values': hgt.tolist(),
                'label': 'Height (m)'
            },
        'start_point': {
                'lon': round(xl[0], 4),
                'lat': round(yl[0], 4)
            },
        'end_point':{
                'lon': round(xl[-1], 4),
                'lat': round(yl[-1], 4)
            }
    }

def vcross_format_params(params):
    pars = params.copy()
    tmp = checkParamInteger(pars, 'radarID')
    if tmp['status'] == -1: return tmp
    pars = tmp['params']
    tmp = checkParamBoolean(pars, 'segment', True)
    if tmp['status'] == -1: return tmp
    pars = tmp['params']

    keys = ['startLon', 'startLat', 'endLon', 'endLat']
    for key in keys:
        tmp = checkParamFloat(pars, key)
        if tmp['status'] == -1:
            return tmp
        pars = tmp['params']
    return {'params': pars, 'status': 0}
