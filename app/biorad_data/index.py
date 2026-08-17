from flask import Blueprint
from flask import current_app as app

from app.scripts.util import response_download_data
from .scripts import (
            get_vp_json,
            get_vpts_json,
            get_vtip_json,
            get_sevip_json,
            anime_gif_sevip,
            get_vp_image,
            get_vpts_image,
            get_vtip_image,
            get_vp_time_range,
            get_vid_time_range,
            get_region_vid_json
        )

biorad_data = Blueprint('biorad_data', __name__)

@biorad_data.route('/get_vp', methods=['GET', 'POST'])
def get_vp():
    """Vertical profiles."""
    return response_download_data(get_vp_json)

@biorad_data.route('/get_vpts', methods=['GET', 'POST'])
def get_vpts():
    """Vertical profiles time series."""
    return response_download_data(get_vpts_json)

@biorad_data.route('/get_vtip', methods=['GET', 'POST'])
def get_vtip():
    """Vertical and time integration of profiles."""
    return response_download_data(get_vtip_json)

@biorad_data.route('/get_sevip', methods=['GET', 'POST'])
def get_sevip():
    """Spatial estimates of vertically integrated parameters."""
    return response_download_data(get_sevip_json)

@biorad_data.route('/get_sevip_gif', methods=['GET', 'POST'])
def get_sevip_gif():
    """GIF Spatial estimates of vertically integrated parameters."""
    return response_download_data(anime_gif_sevip)

@biorad_data.route('/image_vp', methods=['GET', 'POST'])
def image_vp():
    """Plot vertical profiles."""
    return response_download_data(get_vp_image)

@biorad_data.route('/image_vpts', methods=['GET', 'POST'])
def image_vpts():
    """Plot vertical profiles time series."""
    return response_download_data(get_vpts_image)

@biorad_data.route('/image_vtip', methods=['GET', 'POST'])
def image_vtip():
    """Plot vertical and time integration of profiles."""
    return response_download_data(get_vtip_image)

@biorad_data.route('/get_region_vid', methods=['POST'])
def get_region_vid():
    """Polygon aggregation of vertically integrated parameters (analytics)."""
    return response_download_data(get_region_vid_json)

@biorad_data.route('/vp_temporal_coverage', methods=['GET', 'POST'])
def vp_temporal_coverage():
    """Temporal coverage for all vertical profiles products."""
    return response_download_data(get_vp_time_range)

@biorad_data.route('/vid_temporal_coverage', methods=['GET', 'POST'])
def vid_temporal_coverage():
    """Temporal coverage for all vertically integrated parameters."""
    return response_download_data(get_vid_time_range)
