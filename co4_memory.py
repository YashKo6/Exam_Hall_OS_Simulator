"""CO4 - Seating plans as pages, LRU / FIFO page replacement."""
from collections import OrderedDict, deque

PAGE_SIZE = 10  # seats per page

DEFAULT_REFERENCE = "A0 B0 A0 C0 A0 B0 D0 A0 B0 C0 A0 B0 A1 A0 B0 D0"


def page_of(hall_letter, seat_no):
    """Seat 1-10 -> page 0, seat 11-20 -> page 1, ... e.g. ('A', 37) -> 'A3'."""
    return f"{hall_letter}{(seat_no - 1) // PAGE_SIZE}"


def parse_reference(text):
    return [t.strip().upper() for t in text.replace(",", " ").split() if t.strip()]


def lru(ref, frames):
    cache, steps, faults = OrderedDict(), [], 0
    for i, p in enumerate(ref, 1):
        evicted = None
        if p in cache:
            cache.move_to_end(p)
            result = "HIT"
        else:
            faults += 1
            result = "FAULT"
            if len(cache) >= frames:
                evicted, _ = cache.popitem(last=False)   # least recently used
            cache[p] = True
        steps.append(dict(step=i, page=p, frames=list(cache), result=result, evicted=evicted))
    return _summary(steps, ref, faults)


def fifo(ref, frames):
    q, steps, faults = deque(), [], 0
    for i, p in enumerate(ref, 1):
        evicted = None
        if p in q:
            result = "HIT"
        else:
            faults += 1
            result = "FAULT"
            if len(q) >= frames:
                evicted = q.popleft()
            q.append(p)
        steps.append(dict(step=i, page=p, frames=list(q), result=result, evicted=evicted))
    return _summary(steps, ref, faults)


def _summary(steps, ref, faults):
    n = len(ref)
    return dict(steps=steps, faults=faults, hits=n - faults,
                ratio=(n - faults) / n if n else 0)
