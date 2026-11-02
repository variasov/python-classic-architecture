from library.composites.infra.db.engine import engine
from library.infra.db.gateways.readers_search_gateway import DbReadersSearchGateway

readers_search_gateway = DbReadersSearchGateway(engine=engine)
