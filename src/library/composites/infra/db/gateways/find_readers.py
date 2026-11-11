from library.composites.infra.db.engine import engine
from library.infra.db.gateways.find_readers import DbFindReadersGateway

find_readers_gateway = DbFindReadersGateway(engine)
