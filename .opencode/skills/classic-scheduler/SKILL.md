---
name: classic-scheduler
description: Справка по API библиотеки classic-scheduler 2.x (classic.scheduler) - Scheduler, задачи by_cron, by_period, with_delay, ScheduledJob и отмена, часовой пояс, запуск run/start, остановка stop/join. Загружать перед написанием кода с classic.scheduler. Как планировщик применяется в архитектуре - в python-classic-composite.
license: MIT
compatibility: opencode
---

# classic-scheduler 2.x: API

Только API, сверенный с версией 2.0. Правила применения (точка входа планировщика, что вызывает задача) - в `python-classic-composite`.

```python
from zoneinfo import ZoneInfo

from classic.scheduler import Scheduler

scheduler = Scheduler(tz=ZoneInfo('Europe/Moscow'))   # workers_num=1; tz - для cron-задач
job = scheduler.by_cron('0 9 * * *', remind_overdue_loans.run)
scheduler.run()                    # блокирует поток до stop() или Ctrl+C
```

## Задачи
Общие параметры: `job` - callable, `args: tuple | None`, `kwargs: dict | None`. Все методы возвращают `ScheduledJob`.
- `by_cron(schedule: str, job, args=None, kwargs=None, tz=None)` - по cron-строке (5 полей, 6-е в конце - секунды). Часовой пояс: `tz` задачи, иначе `tz` планировщика, иначе локальный.
- `by_period(period: float | timedelta, job, ...)` - сразу и затем каждые `period` секунд.
- `with_delay(delay: float | timedelta, job, ...)` - один раз через `delay`.
- `job.cancel()` - отменить задачу (асинхронно, повторно - безопасно). Параметра `task_name` и `Scheduler.cancel(name)` в 2.x нет.
- Если предыдущий запуск задачи ещё идёт, очередной пропускается с WARNING.
- Исключение в задаче логируется (`classic.scheduler.task`, ERROR) и не останавливает планировщик.
- Задачи можно добавлять до и после запуска, из любого потока.

## Запуск и остановка
- `run()` - цикл в текущем потоке. Использовать только в `__main__.py`. Повторный `run()` при работающем - `RuntimeError`.
- `start(daemon=False)` - запуск в фоновом потоке, возвращает `None`. Поток по умолчанию не daemon: без `stop()` процесс не завершится.
- `stop(block=False, timeout=None)` - остановка; `block=True` ждёт фоновый поток.
- `join(timeout=None)`, `is_alive()`.
- После `stop()` можно запустить снова, задачи сохраняются.

## Тесты
- Задачу проверяют, вызывая её `job` напрямую (метод usecase из композита), а не ожидая срабатывания расписания.
- Публичного списка задач нет. Регистрацию проверяй через собственную функцию сборки, принимающую `Scheduler`: в тесте передай fake с `by_cron`, записывающим вызовы.
- Если всё же нужен запуск: `start()` + короткий `with_delay` + `stop(block=True, timeout=...)`.
