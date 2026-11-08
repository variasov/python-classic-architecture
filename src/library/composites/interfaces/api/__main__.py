import waitress

from library.composites.interfaces.api.settings import settings
from library.composites.interfaces.api.wsgi import app

waitress.serve(
    app,
    host=settings.API_HOST,
    port=settings.API_PORT,
)
