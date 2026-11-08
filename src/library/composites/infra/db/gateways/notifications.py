from library.composites.infra.db.engine import engine
from library.infra.db.gateways.notifications import (
    NotificationsGatewayImpl,
)

notifications_gateway = NotificationsGatewayImpl(db=engine)
