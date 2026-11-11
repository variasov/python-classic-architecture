---
name: classic-scheduler
description: Справка по API библиотеки classic-scheduler (classic.scheduler) - Scheduler, задачи by_cron, by_period, with_delay, запуск run/start, остановка, отмена задач. Загружать перед написанием кода с classic.scheduler. Как планировщик применяется в архитектуре - в python-classic-composite.
license: MIT
compatibility: opencode
---

# classic-scheduler: API

Только API, сверенный с версией 1.4. Правила применения (точка входа планировщика, что вызывает задача) - в `python-classic-composite`.

```python
from classic.scheduler import Scheduler

scheduler = Scheduler()            # workers_num=1; 0 - задачи в потоке планировщика
scheduler.by_cron(
    schedule='0 9 * * *',
    job=lambda: hub.notify(DailyCheck()),
    task_name='daily_check',
)
scheduler.run()                    # блокирует поток навсегда
```

## Задачи
Общие параметры: `job` - callable, `args: tuple = None`, `kwargs: dict = None`, `task_name: str = None`.
- `by_cron(schedule: str, job, ...)` - по cron-строке (5 полей).
- `by_period(period: float | timedelta, job, ...)` - сразу и затем каждые `period` (секунды).
- `with_delay(delay: float | timedelta, job, ...)` - один раз через `delay`.
- `cancel(task_name)` - отменить задачу по имени; неизвестное имя молча игнорируется.
- Задачи можно добавлять до и после запуска.

## Запуск и остановка
- `run()` - вечный цикл в текущем потоке. Использовать только в `__main__.py`.
- `start()` - запускает `run()` в фоновом daemon-потоке и возвращает ident потока.
- `stop()` - асинхронно ставит остановку в очередь; ждать завершения - `join(timeout=None)`. В этой версии у `stop()` нет параметров `block`/`timeout`, хотя README их упоминает.
- `is_alive()` - работает ли фоновый поток.

## Тесты
- Задачу проверяют, вызывая её `job` напрямую (вынеси job в именованную функцию/метод композита), а не ожидая срабатывания расписания.
- Регистрацию задачи проверяют на собранном инстансе планировщика без `run()`. Публичного списка задач нет, а `cancel` неизвестного имени не бросает ошибку - поэтому регистрацию проверяй через собственную функцию сборки (например, она принимает `Scheduler` и в тесте получает fake с `by_cron`, записывающим вызовы).
- Если всё же нужен запуск: `start()` + короткий `by_period`/`with_delay` + `stop()` и `join(timeout=...)`.
