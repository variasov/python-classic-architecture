import waitress

from library.composites.interfaces.web_api.settings import api_settings
from library.composites.interfaces.web_api.wsgi import app

waitress.serve(app, host=api_settings.API_HOST, port=api_settings.API_PORT)
