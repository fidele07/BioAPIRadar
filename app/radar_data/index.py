from flask import Blueprint, request
from flask import make_response, jsonify
from flask import current_app as app
import json
import os

radar_data = Blueprint('radar_data', __name__)
