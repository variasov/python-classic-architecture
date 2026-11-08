from library.app.errors import AppError


class EntityNotSaved(AppError):
    def __str__(self) -> str:
        return 'Сущность должна быть сохранена перед получением id'


def saved_id(value: int | None) -> int:
    if value is None:
        raise EntityNotSaved
    return value
