import waitress
from library.composites.interfaces.api.settings import api_settings
from library.composites.interfaces.api.wsgi import app

waitress.serve(app, host=api_settings.API_HOST, port=api_settings.API_PORT)
