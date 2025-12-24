import os
import glob
import numpy as np
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import (
            response_download_error,
            response_download_json,
            get_data_dates_dir
        )
import xradar as xd
from pyproj import CRS, Transformer
from app.scripts.cdb import queryDB_json
from BioModRadar import read_xradar_data

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

def get_sweeps_fixed_angles(dtree):
    sweeps = xd.util.get_sweep_keys(dtree)
    fixed_angles = []
    for s in sweeps:
       fixed_angles += [dtree[s]['sweep_fixed_angle'].values]
    return np.array(sweeps), np.array(fixed_angles)

def get_dtree_lat_lon_alt(ds):
    ds = ds.copy()
    ds = ds.xradar.georeference()
    src_crs = xd.georeference.projection.get_crs(ds, datum='WGS84')
    trg_crs = CRS.from_user_input(4326)
    transformer = Transformer.from_crs(src_crs, trg_crs)
    return transformer.transform(ds.x, ds.y, ds.z)

def get_elevation_angles(params):
    polar_id = f'polar_{params['radarID']}'
    polar_info = GLOBAL_CONFIG['radar'][polar_id]
    dates_dir = get_data_dates_dir(polar_info)
    if dates_dir is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'elevation_angles', 422
            )

    first_file = []
    for d in dates_dir:
        data_dir = os.path.join(polar_info['dir'], d)
        data_files = glob.glob(f'{data_dir}/{polar_info['pattern1']}')
        if len(data_files) > 0:
            first_file += [data_files[0]]
            break

    if len(first_file) == 0:
        msg = 'No data found.'
        return response_download_error(
                msg, 'elevation_angles', 422
            )

    field_name = get_field_info('ref')['field']
    fields_dict = {'ref': field_name}
    dtree = read_xradar_data(
            first_file[0],
            volume_type=polar_info['format_vol'],
            fields_dict=fields_dict
        )
    # elv_angles = dtree.sweep_fixed_angle.values
    _, elv_angles = get_sweeps_fixed_angles(dtree)
    return response_download_json(
                elv_angles.tolist(), 'elevation_angles'
            )

def get_rpolar_time_range(params):
    trg = queryDB_json("""
            SELECT start_time, end_time
            FROM rpolar_timerange
            WHERE radar_id=%s;
            """, (params['radarID'],)
        )
    frmt = '%Y-%m-%d %H:%M:%S'
    trg1 = trg[0]['start_time'].strftime(frmt)
    trg2 = trg[0]['end_time'].strftime(frmt)
    temp_cov = {
        'start_time': trg1, 
        'end_time': trg2
    }
    return response_download_json(
                temp_cov, 'rpolar_temporal_coverage'
            )

