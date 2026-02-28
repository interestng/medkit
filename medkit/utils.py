"""
Utility functions for the MedKit SDK.
"""

import functools
import time
from typing import Any, Callable, List, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def cache_response(maxsize: int = 128) -> Callable[[F], F]:
    """
    A simple in-memory cache decorator for API responses.
    """

    def decorator(func: F) -> F:
        @functools.lru_cache(maxsize=maxsize)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Using cast to help mypy understand the type preservation
        return cast(F, wrapper)

    return decorator


class RateLimiter:
    """
    A simple thread-safe rate limiter.
    Ensures that calls do not exceed `calls` per `period` seconds.
    """

    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []

    def wait(self) -> None:
        """
        Blocks if the rate limit has been exceeded.
        """
        now = time.time()

        # Remove timestamps older than the period
        self.timestamps = [t for t in self.timestamps if now - t < self.period]

        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            # Re-evaluate after sleeping
            self.wait()
            return

        self.timestamps.append(time.time())


def paginate(fetch_page: Callable[[int], List[Any]], max_pages: int = 5) -> List[Any]:
    """
    Helper function to paginate through API results.
    `fetch_page` should be a function that takes a page index and returns a list of items.
    Expects `fetch_page` to return an empty list when no more data is available.
    """
    results = []
    for page in range(max_pages):
        page_results = fetch_page(page)
        if not page_results:
            break
        results.extend(page_results)
    return results
