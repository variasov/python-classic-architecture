---
name: classic-signals
description: Справка по API библиотеки classic-signals 1.x (classic.signals) - Hub, add_reaction, remove_reaction, notify, порядок и поток выполнения реакций. Загружать перед написанием кода с classic.signals.Hub. Как сигналы применяются в архитектуре - в python-classic-app и python-classic-composite.
license: MIT
compatibility: opencode
---

# classic-signals 1.x: API

Только API, сверенный с версией 1.1. Правила применения (где объявлять сигналы, где жить подписчикам, где инстанс Hub) - в `python-classic-app` и `python-classic-composite`.

```python
from dataclasses import dataclass

from classic.signals import Hub


@dataclass(frozen=True)
class LoanIssued:          # сигнал - любой объект, обычно датакласс
    loan_id: int


class NotifyOnLoanIssued:
    def __init__(self, hub: Hub) -> None:
        hub.add_reaction(LoanIssued, self._on_loan_issued)

    def _on_loan_issued(self, signal: LoanIssued) -> None:
        ...


hub = Hub()
NotifyOnLoanIssued(hub=hub)
hub.notify(LoanIssued(loan_id=1))
```

- `Hub()` - без аргументов. Публичные методы: `add_reaction`, `remove_reaction`, `notify`.
- `hub.add_reaction(SignalCls, reaction)` - реакция: любой callable с одним аргументом (инстанс сигнала). Повторная регистрация той же реакции игнорируется.
- `hub.remove_reaction(SignalCls, reaction)` - отписка.
- `hub.notify(*signals)` - вызывает реакции синхронно, в текущем потоке, в порядке регистрации; можно передать несколько сигналов.
- Реакции ищутся по точному классу сигнала, наследование не учитывается: реакция на базовый класс не вызывается для наследника.
- Исключение в реакции прерывает оставшиеся реакции и пробрасывается из `notify`: в той же транзакции это откатит всю операцию.
- Вызывать `add_reaction`/`remove_reaction` из реакции нельзя - взаимоблокировка.
- Нет реакций - `notify` ничего не делает, ошибки нет.

## Тесты
Свой `Hub()` в тесте + реакция, накапливающая сигналы:
```python
received: list[LoanIssued] = []
hub.add_reaction(LoanIssued, received.append)
```
