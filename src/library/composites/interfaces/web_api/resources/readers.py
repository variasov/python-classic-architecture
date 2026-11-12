from library.composites.app.commands.readers.register_reader import (
    register_reader,
)
from library.composites.app.queries.readers.find_readers import find_readers
from library.interfaces.web_api.resources.readers import ReadersResource

readers = ReadersResource(
    find_readers=find_readers,
    register_reader=register_reader,
)
