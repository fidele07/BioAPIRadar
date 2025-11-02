from flask import Blueprint, request
from flask import current_app as app

from app.scripts.util import (
        response_download_data,
        post_get_request
    )
from .scripts.rgrid import download_grid
from .scripts.rpolar import download_polar
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

