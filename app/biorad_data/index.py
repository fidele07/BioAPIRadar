from flask import Blueprint
from flask import current_app as app

from app.scripts.util import response_download_data
from .scripts import (
            download_vp,
            download_vpts,
            download_vtip,
            download_sevip,
            anime_gif_sevip,
            get_vpts_image,
            get_vtip_image
        )

biorad_data = Blueprint('biorad_data', __name__)

@biorad_data.route('/get_vp', methods=['GET', 'POST'])
def get_vp():
    """Vertical profiles."""
    return response_download_data(download_vp)

@biorad_data.route('/get_vpts', methods=['GET', 'POST'])
def get_vpts():
    """Vertical profiles time series."""
    return response_download_data(download_vpts)

@biorad_data.route('/get_vtip', methods=['GET', 'POST'])
def get_vtip():
    """Vertical and time integration of profiles."""
    return response_download_data(download_vtip)

@biorad_data.route('/get_sevip', methods=['GET', 'POST'])
def get_sevip():
    """Spatial estimates of vertically integrated parameters."""
    return response_download_data(download_sevip)

@biorad_data.route('/get_sevip_gif', methods=['GET', 'POST'])
def get_sevip_gif():
    """GIF Spatial estimates of vertically integrated parameters."""
    return response_download_data(anime_gif_sevip)

@biorad_data.route('/image_vpts', methods=['GET', 'POST'])
def image_vpts():
    """Plot vertical profiles time series."""
    return response_download_data(get_vpts_image)

@biorad_data.route('/image_vtip', methods=['GET', 'POST'])
def image_vtip():
    """Plot vertical and time integration of profiles."""
    return response_download_data(get_vtip_image)
