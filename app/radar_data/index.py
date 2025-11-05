from flask import Blueprint, request
from flask import current_app as app

from app.scripts.util import (
        response_download_data,
        post_get_request
    )
from .scripts.rgrid import download_grid
from .scripts.rpolar import download_polar
from .scripts.vgrid import vcross_section_grid
from .scripts.vpolar import vcross_section_polar
from .scripts.rinfo import get_elevation_angles

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
