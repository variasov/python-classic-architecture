from library.composites.infra.db.engine import engine
from library.infra.db.repos.notifications import DbNotificationsRepo

notifications_repo = DbNotificationsRepo(engine)
