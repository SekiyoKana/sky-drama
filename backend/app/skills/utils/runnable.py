import threading
import queue
from typing import Generator, Any, Callable


def run_in_thread_and_stream(
    func: Callable, *args, **kwargs
) -> Generator[Any, None, None]:
    """
    Run the given function in a separate thread.
    The function should return an iterable (generator).
    This function returns a generator that yields items from the function's output queue.
    """
    q = queue.Queue()

    def producer():
        try:
            result = func(*args, **kwargs)
            if hasattr(result, "__iter__") and not isinstance(result, (str, dict)):
                for item in result:
                    q.put(item)
            else:
                # If it's a single value, just put it
                q.put(result)
        except Exception as e:
            import traceback

            traceback.print_exc()
            q.put({"type": "error", "content": str(e)})
        finally:
            q.put(None)  # Sentinel

    t = threading.Thread(target=producer, daemon=True)
    t.start()

    while True:
        item = q.get()
        if item is None:
            break
        yield item
