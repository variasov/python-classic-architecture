from datetime import date
from typing import Any

from classic.criteria import Criteria
from classic.db_tools import Engine, Entity

from library.app.domain.notification import (
    Notification,
    NotificationKind,
    NotificationNotFound,
    NotificationsRepo,
)


def _notification(
    reader_id: int,
    loan_id: int,
    kind: str,
    created_at: date,
    id: int,
) -> Notification:
    """Собирает уведомление, переводя вид из текста в перечисление."""
    return Notification(
        reader_id=reader_id,
        loan_id=loan_id,
        kind=NotificationKind(kind),
        created_at=created_at,
        id=id,
    )


class DbNotificationsRepo(NotificationsRepo):
    """Репозиторий уведомлений поверх PostgreSQL."""

    def __init__(self, db: Engine[Any]) -> None:
        self._db = db

    def get_by_id(self, id: int) -> Notification:
        notification: Notification | None = (
            self._db.query_from('aggregates/notifications/get_by_id.sql')
            .map_to(Notification, Notification=Entity(_notification, 'id'))
            .one(id=id)
        )
        if notification is None:
            raise NotificationNotFound(id=id)
        return notification

    def save(self, notification: Notification) -> Notification:
        notification.check()
        params = self._params(notification)
        if notification.id is None:
            notification.id = self._db.query_from(
                'aggregates/notifications/insert.sql',
            ).scalar(**params)
        else:
            updated = self._db.query_from(
                'aggregates/notifications/update.sql',
            ).scalar(**params)
            if updated is None:
                raise NotificationNotFound(id=notification.id)
        return notification

    def find(self, criteria: Criteria[Notification]) -> list[Notification]:
        notifications: list[Notification] = (
            self._db.query_from('aggregates/notifications/find.sql.tmpl')
            .map_to(Notification, Notification=Entity(_notification, 'id'))
            .all(criteria=criteria)
        )
        return notifications

    def _params(self, notification: Notification) -> dict[str, Any]:
        return {
            'id': notification.id,
            'reader_id': notification.reader_id,
            'loan_id': notification.loan_id,
            'kind': notification.kind.value,
            'created_at': notification.created_at,
        }
