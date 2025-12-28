from app.scripts.cdb import queryDB_json
from app.scripts.util import response_download_json

def get_vp_time_range(params):
    trg = queryDB_json("""
            SELECT start_time, end_time
            FROM vp_timerange
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
                temp_cov, 'vp_temporal_coverage'
            )

def get_vid_time_range(params):
    trg = queryDB_json("""
            SELECT start_time, end_time
            FROM vid_timerange
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
                temp_cov, 'vid_temporal_coverage'
            )

