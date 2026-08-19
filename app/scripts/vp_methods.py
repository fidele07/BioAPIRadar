from app.scripts.cdb import queryDB_json
from app.scripts.util import response_download_json


def get_vp_methods_coverage(params):
    """Species-separation provenance for a time range (dashboard tags).

    Every per-species number a dashboard shows must say which method
    produced it. Returns the vp_polar `method` values present in the
    range with scan counts, e.g.:

        {"methods": [{"method": "legacy_rcs_ratio", "n": 1152},
                     {"method": "step1_sdvvp", "n": 288}]}

    Method values:
      legacy_rcs_ratio : pre-fix rows — one measurement under two RCS
                         labels; NOT a species measurement
      step1_sdvvp      : per-layer sd_vvp partition (reprocessed)
      gmm_partition    : profile-level statistical partition (interim,
                         legacy archive)
      step2_dualpol    : gate-level dual-pol classification (final)

    The function name carries 'coverage' so the response cache exempts
    it — the boundary between methods moves as reprocessing advances.
    """
    start = params.get('startTime') or params.get('time')
    end = params.get('endTime') or params.get('time')
    rows = queryDB_json(
        """
        SELECT coalesce(method, 'legacy_rcs_ratio') AS method,
               count(*) AS n
        FROM vp_polar
        WHERE radar_id = %s
          AND date_time BETWEEN %s::timestamp AND %s::timestamp
        GROUP BY 1 ORDER BY 2 DESC;
        """,
        (params['radarID'], start, end)
    )
    return response_download_json({'methods': rows}, 'vp_methods')
