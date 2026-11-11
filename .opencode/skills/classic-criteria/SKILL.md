---
name: classic-criteria
description: Справка по API библиотеки classic-criteria (classic.criteria) - декоратор @criteria, две формы вызова (на инстансе и ленивая на классе), Criteria[T], комбинации &, |, ~, is_satisfied_by, типизация. Загружать перед написанием кода с classic.criteria. Как критерии применяются в архитектуре - в python-classic-domain, трансляция в SQL - в classic-db-tools.
license: MIT
compatibility: opencode
---

# classic-criteria: API

Только API, сверенный с версией 0.2. Правила применения (когда какая форма, имена, запрет `must_be_satisfied`) - в `python-classic-domain`.

## Объявление
```python
from dataclasses import dataclass
from datetime import date

from classic.criteria import Criteria, criteria


@dataclass
class Loan:
    due: date
    returned_at: date | None = None

    @criteria
    def overdue(self, on: date) -> bool:
        return self.returned_at is None and self.due < on

    @criteria
    def returned(self) -> bool:
        return self.returned_at is not None
```
- Первый параметр - кандидат (`self`), остальные - параметры критерия. Из них строится датакласс критерия, поэтому параметры должны быть аннотированы (дефолты допустимы).
- Сгенерированный класс критерия называется как функция (`overdue`). По этому имени `traverse` в classic-db-tools ищет SQL-макрос.

## Две формы вызова
| Вызов | Результат |
|---|---|
| `loan.overdue(on=today)` | `bool` - проверка сразу |
| `Loan.overdue(on=today)` | `Criteria[Loan]` - ленивый объект, ничего не проверяет |

Ленивый объект:
- `crit.is_satisfied_by(loan) -> bool`; `crit(loan)` - то же (удобно для `filter(crit, loans)`);
- параметры доступны атрибутами: `Loan.overdue(on=today).on`;
- `crit.must_be_satisfied_by(loan)` бросает `CriteriaNotSatisfied`. Это наследник `BaseException`, а не `Exception`: `except Exception` его не ловит.

На инстансе также есть `loan.overdue.must_be_satisfied(on=today)`.

## Комбинации
```python
crit = Loan.overdue(on=today) & ~Loan.returned()
crit = Reader.membership_active(on=today) | Reader.vip()
```
- `&` → `And`, `|` → `Or`, `~` → `Invert`, `^` → `Xor`; результат - снова `Criteria[T]`.
- Узлы: `And.nested` / `Or.nested` - список вложенных, `Invert.nested` - один вложенный.
- Комбинации работают только для ленивой формы. На инстансе результат - `bool`, комбинируй через `and`/`or`/`not`.

## Типизация
- В сигнатурах портов - `Criteria[Loan]`: `def find(self, criteria: Criteria[Loan]) -> list[Loan]: ...`.
- In-memory реализация: `[l for l in items if criteria.is_satisfied_by(l)]`.

## Критерии-классы (альтернатива декоратору)
```python
@dataclass
class Overdue(Criteria[Loan]):
    on: date

    def is_satisfied_by(self, candidate: Loan) -> bool:
        return candidate.returned_at is None and candidate.due < self.on
```
Используются, когда критерий не принадлежит одному классу. В домене демо - декоратор на методах агрегата.
