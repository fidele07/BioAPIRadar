from flask import Blueprint, request
from flask import current_app as app

from app.scripts.util import (
        response_download_data,
        post_get_request
    )
from .scripts import *

radar_data = Blueprint('radar_data', __name__)

@radar_data.route('/get_radar', methods=['GET', 'POST'])
def get_radar():
    """Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(download_polar_0)
        # return response_download_data(download_polar_1)
    else:
        return response_download_data(download_grid)

@radar_data.route('/elevation_angles', methods=['GET', 'POST'])
def elevation_angles():
    """Elevation angles."""
    return response_download_data(get_elevation_angles_0)
    # return response_download_data(get_elevation_angles_1)

@radar_data.route('/vcross_section_radar', methods=['GET', 'POST'])
def vcross_section_radar():
    """Vertical Cross-Section Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(vcross_section_polar_0)
        # return response_download_data(vcross_section_polar_1)
    else:
        return response_download_data(vcross_section_grid)

@radar_data.route('/vcross_section_image', methods=['GET', 'POST'])
def vcross_section_image():
    """Image Vertical Cross-Section Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(image_vcross_section_polar_0)
        # return response_download_data(image_vcross_section_polar_1)
    else:
        return response_download_data(image_vcross_section_grid)

@radar_data.route('/get_radar_gif', methods=['GET', 'POST'])
def get_radar_gif():
    """GIF Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(anime_gif_polar_0)
        # return response_download_data(anime_gif_polar_1)
    else:
        return response_download_data(anime_gif_grid)

@radar_data.route('/rpolar_temporal_coverage', methods=['GET', 'POST'])
def rpolar_temporal_coverage():
    """Temporal coverage for polar radar data."""
    return response_download_data(get_rpolar_time_range)
