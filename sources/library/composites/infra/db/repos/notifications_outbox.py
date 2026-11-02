from library.composites.infra.db.engine import engine
from library.infra.db.repos.notifications_outbox import DbNotificationsOutbox

notifications_outbox = DbNotificationsOutbox(engine=engine)
