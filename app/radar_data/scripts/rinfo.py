import os
import glob
from datetime import datetime
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import (
            response_download_error,
            response_download_json
        )
import pyart

def get_field_info(field):
    radar_fields = [
            {'id': 'ref', 'field': 'DBZH', 'name': 'Reflectivity', 'units': 'dBZ'},
            {'id': 'zdr', 'field': 'ZDR', 'name': 'Differential Reflectivity', 'units': 'dB'},
            {'id': 'phi', 'field': 'PHIDP', 'name': 'Differential Phase', 'units': 'degrees'},
            {'id': 'rho', 'field': 'RHOHV', 'name': 'Correlation Coefficient', 'units': ''},
            {'id': 'vel', 'field': 'VRADH', 'name': 'Radial Velocity', 'units': 'm/s'},
            {'id': 'sw', 'field': 'WRADH', 'name': 'Spectrum Width', 'units': 'm/s'},
            {'id': 'dr', 'field': 'DR', 'name': 'Depolarization Ratio', 'units': 'dB'}
        ]
    return [f for f in radar_fields if f['id'] == field][0]

def get_elevation_angles(params):
    polar_info = GLOBAL_CONFIG['radar']['polar']
    dates_dir = polar_info['dir']
    tmp_path = [os.path.join(dates_dir, d) for d in os.listdir(dates_dir)]

    if len(tmp_path) == 0:
        msg = 'No data found.'
        return response_download_error(
                msg, 'elevation_angles', 422
            )

    dates_dir = [os.path.basename(d) for d in tmp_path if os.path.isdir(d)]

    tmp_path = []
    for d in dates_dir:
        try:
            tmp = datetime.strptime(d, polar_info['format_dir'])
            tmp_path += [d]
        except:
            continue

    if len(tmp_path) == 0:
        msg = 'No data found.'
        return response_download_error(
                msg, 'elevation_angles', 422
            )

    first_file = []
    for d in tmp_path:
        data_dir = os.path.join(polar_info['dir'], d)
        data_files = glob.glob(f'{data_dir}/{polar_info['pattern']}')
        if len(data_files) > 0:
            first_file += [data_files[0]]
            break

    if len(first_file) == 0:
        msg = 'No data found.'
        return response_download_error(
                msg, 'elevation_angles', 422
            )

    field_name = get_field_info('ref')['field']
    radar = pyart.aux_io.read_odim_h5(
            first_file[0], include_fields=[field_name],
            file_field_names=True, delay_field_loading=True
        )
    elv_angles = radar.fixed_angle['data'].tolist()
    return response_download_json(
                elv_angles, params, 'elevation_angles'
            )
