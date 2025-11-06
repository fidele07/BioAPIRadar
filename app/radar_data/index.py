from flask import Blueprint, request
from flask import current_app as app

from app.scripts.util import (
        response_download_data,
        post_get_request
    )
from .scripts import (
        download_grid,
        download_polar,
        vcross_section_grid,
        vcross_section_polar,
        get_elevation_angles,
        anime_gif_grid,
        anime_gif_polar
    )

radar_data = Blueprint('radar_data', __name__)

@radar_data.route('/get_radar', methods=['GET', 'POST'])
def get_radar():
    """Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(download_polar)
    else:
        return response_download_data(download_grid)

@radar_data.route('/elevation_angles', methods=['GET', 'POST'])
def elevation_angles():
    """Elevation angles."""
    return response_download_data(get_elevation_angles)

@radar_data.route('/vcross_section_radar', methods=['GET', 'POST'])
def vcross_section_radar():
    """Vertical Cross-Section Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(vcross_section_polar)
    else:
        return response_download_data(vcross_section_grid)

@radar_data.route('/get_radar_gif', methods=['GET', 'POST'])
def get_radar_gif():
    """GIF Radar data."""
    params = post_get_request()
    if params['type'] == 'polar':
        return response_download_data(anime_gif_polar)
    else:
        return response_download_data(anime_gif_grid)
