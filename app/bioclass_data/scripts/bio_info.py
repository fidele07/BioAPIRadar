from app.scripts.util import (
            response_download_error,
            response_download_json,
        )
from app.scripts.cdb import queryDB_json

def get_class_info(field):
    radar_fields = [
            {
                'id': 'species', 'field': 'BIO_CLASS',
                'class_0': 'Insect', 'class_1': 'Bird',
                'name': 'Bird vs Insect Classification'
            },
            {
                'id': 'biometeo', 'field': 'DR_CLASS',
                'class_0': 'Meteorological', 'class_1': 'Biological',
                'name': 'Biological vs Meteorological Classification'
            }
        ]
    return [f for f in radar_fields if f['id'] == field][0]

def get_bioclass_time_range(params):
    trg = queryDB_json("""
            SELECT start_time, end_time
            FROM bioclass_timerange
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
                temp_cov, 'bioclass_temporal_coverage'
            )
