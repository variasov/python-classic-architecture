from library.composites.infra.db.engine import engine
from library.infra.db.gateways.find_readers import FindReadersGatewayImpl

find_readers_gateway = FindReadersGatewayImpl(db=engine)
