from demo.app.commands.domain.aggregates.cat import Movement


def build_movement(row: tuple) -> Movement:
    return Movement(
        timestamp=row[0],
        latitude=row[1],
        longitude=row[2],
    )
