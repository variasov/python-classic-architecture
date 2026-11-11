from library.app.queries.readers.find_readers import FindReaders
from library.composites.infra.db.gateways.find_readers import find_readers_gateway

find_readers = FindReaders(gateway=find_readers_gateway)
