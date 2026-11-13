"""Bounded request queue: at most one in-flight task per worker."""
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
def bounded_map(fn,items,workers):
    iterator=iter(items)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        active={pool.submit(fn,item) for item in __import__('itertools').islice(iterator,workers)}
        try:
            while active:
                done,active=wait(active,return_when=FIRST_COMPLETED)
                results=[future.result() for future in done]
                for result in results:yield result
                for _ in done:
                    item=next(iterator,None)
                    if item is not None:active.add(pool.submit(fn,item))
        except BaseException:
            for future in active:future.cancel()
            raise

