import functools
import time
from collections.abc import Callable
from typing import Final, ParamSpec, TypeVar

P = ParamSpec('P')
T = TypeVar('T')

ATTEMPTS: Final[int] = 3
INITIAL_DELAY: Final[float] = 0.1


def retry_on_failure(fn: Callable[P, T]) -> Callable[P, T]:
    """Повторить вызов до трёх раз с экспоненциальной паузой.

    После последней неудачной попытки пробрасывается исходное исключение.
    """

    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        attempts_left = ATTEMPTS
        while True:
            try:
                return fn(*args, **kwargs)
            except Exception:
                attempts_left -= 1
                if attempts_left <= 0:
                    raise
                time.sleep(INITIAL_DELAY * 2 ** (ATTEMPTS - attempts_left - 1))

    return wrapper
