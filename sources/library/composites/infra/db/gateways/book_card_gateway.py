from library.composites.infra.db.engine import engine
from library.infra.db.gateways.book_card_gateway import DbBookCardGateway

book_card_gateway = DbBookCardGateway(engine=engine)
