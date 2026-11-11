from library.composites.app.commands.register_reader import register_reader
from library.interfaces.api.resources.readers import ReadersResource

readers = ReadersResource(register_reader=register_reader)
