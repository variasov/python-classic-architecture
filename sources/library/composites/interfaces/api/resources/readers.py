from library.composites.app.commands.register_reader import register_reader
from library.composites.app.queries.find_readers import find_readers
from library.interfaces.api.resources.readers import ReadersResource

readers_resource = ReadersResource(
    find_readers=find_readers,
    register_reader=register_reader,
)
