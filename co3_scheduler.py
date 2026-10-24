"""CO3 - FCFS hall allocation, priority invigilator assignment, deadlock detection."""
import copy
import heapq

import data


# ---------------------------------------------------------------- FCFS halls
def fcfs_halls(batches=None, halls=None):
    """Serve batches in arrival order. Each gets the hall (capacity >= students)
    that lets it start earliest (ties -> smaller hall)."""
    batches = sorted(batches or data.BATCHES, key=lambda b: b["arrival"])
    halls = halls or data.HALLS
    free_at = {h: 0 for h in halls}
    rows = []
    for b in batches:
        fits = [h for h, cap in halls.items() if cap >= b["students"]]
        if not fits:
            rows.append(dict(batch=b, hall="NO HALL", start=None, end=None, wait=None, tat=None))
            continue
        hall = min(fits, key=lambda h: (max(free_at[h], b["arrival"]), halls[h]))
        start = max(free_at[hall], b["arrival"])
        end = start + b["duration"]
        free_at[hall] = end
        rows.append(dict(batch=b, hall=hall, start=start, end=end,
                         wait=start - b["arrival"], tat=end - b["arrival"]))
    return rows


def averages(rows, keys=("wait", "tat")):
    ok = [r for r in rows if r.get(keys[0]) is not None]
    return {k: (sum(r[k] for r in ok) / len(ok) if ok else 0) for k in keys}


# ------------------------------------------------- Priority invigilators
def priority_invigilators(hall_rows, invigilators=None, aging=0):
    """Non-preemptive priority scheduling with a min-heap.
    Lower number = higher priority. Free invigilators are picked most-senior first.
    aging > 0: every `aging` minutes of waiting improves priority by 1 (no starvation)."""
    invigilators = invigilators or data.INVIGILATORS
    rank = dict(invigilators)
    free_at = {n: 0 for n, _ in invigilators}
    pending = [dict(r, ready=r["start"]) for r in hall_rows if r["start"] is not None]
    out = []
    t = min(p["ready"] for p in pending) if pending else 0
    while pending:
        ready = [p for p in pending if p["ready"] <= t]
        free = sorted([n for n in free_at if free_at[n] <= t], key=lambda n: rank[n])
        if not ready or not free:
            cands = []
            if not ready:
                cands += [p["ready"] for p in pending if p["ready"] > t]
            if not free:
                cands += [f for f in free_at.values() if f > t]
            t = min(cands)
            continue
        heap = []                                       # (effective priority, arrival, id)
        for p in ready:
            eff = p["batch"]["priority"] - ((t - p["ready"]) // aging if aging else 0)
            heapq.heappush(heap, (eff, p["batch"]["arrival"], p["batch"]["id"], id(p)))
        eff, _, bid, _ = heapq.heappop(heap)
        chosen = next(p for p in ready if p["batch"]["id"] == bid)
        inv = free[0]
        dur = chosen["batch"]["duration"]
        out.append(dict(batch=chosen["batch"], inv=inv, rank=rank[inv], eff=eff,
                        ready=chosen["ready"], start=t, end=t + dur, wait=t - chosen["ready"]))
        free_at[inv] = t + dur
        pending.remove(chosen)
    return out


# ------------------------------------------------------------ Deadlock
DEADLOCK_SCENARIO = {
    "allocation": {"Exam-A": ["Hall 1"], "Exam-B": ["Lab 2"], "Exam-C": ["Projector"]},
    "request":    {"Exam-A": ["Lab 2"],  "Exam-B": ["Hall 1"], "Exam-C": ["Hall 1"]},
    "priority":   {"Exam-A": 2, "Exam-B": 3, "Exam-C": 1},
}
SAFE_SCENARIO = {
    "allocation": {"Exam-A": ["Hall 1"], "Exam-B": ["Lab 2"], "Exam-C": []},
    "request":    {"Exam-A": ["Lab 2"],  "Exam-B": [],         "Exam-C": ["Hall 1"]},
    "priority":   {"Exam-A": 2, "Exam-B": 3, "Exam-C": 1},
}


def wait_for_graph(sc):
    holder = {r: p for p, rs in sc["allocation"].items() for r in rs}
    graph = {p: [] for p in sc["allocation"]}
    for p, rs in sc["request"].items():
        for r in rs:
            h = holder.get(r)
            if h and h != p:
                graph[p].append((h, r))
    return graph


def find_cycle(graph):
    """DFS cycle detection. Returns list of processes in the cycle or None."""
    color, stack = {}, []

    def dfs(u):
        color[u] = 1; stack.append(u)
        for v, _ in graph[u]:
            if color.get(v, 0) == 0:
                c = dfs(v)
                if c: return c
            elif color[v] == 1:
                return stack[stack.index(v):] + [v]
        stack.pop(); color[u] = 2
        return None

    for node in graph:
        if color.get(node, 0) == 0:
            c = dfs(node)
            if c: return c
    return None


def describe_scenario(sc):
    lines = ["Resource allocation (process holds):"]
    for p, rs in sc["allocation"].items():
        lines.append(f"  {p} holds {', '.join(rs) or '-'}")
    lines.append("Pending requests (process wants):")
    for p, rs in sc["request"].items():
        lines.append(f"  {p} requests {', '.join(rs) or '-'}")
    g = wait_for_graph(sc)
    lines.append("Wait-for graph edges:")
    edges = [f"  {p} -> {h}   (waits for {r})" for p, es in g.items() for h, r in es]
    lines += edges or ["  (none)"]
    return lines, g


def detect_deadlock(sc):
    lines, g = describe_scenario(sc)
    cyc = find_cycle(g)
    lines.append("")
    if cyc:
        lines.append("DEADLOCK DETECTED! Cycle: " + " -> ".join(cyc))
    else:
        lines.append("No cycle found: system is deadlock-free.")
    return lines, cyc


def recover(sc, cycle):
    """Preempt the lowest-priority exam in the cycle (largest priority number)."""
    sc = copy.deepcopy(sc)
    victim = max(set(cycle), key=lambda p: sc["priority"][p])
    steps = [f"Recovery: victim chosen = {victim} (lowest priority in cycle)",
             f"  Preempting {victim}: releasing {', '.join(sc['allocation'][victim])}",
             f"  {victim} is rescheduled for a later slot (request cancelled)"]
    sc["allocation"][victim] = []
    sc["request"][victim] = []
    cyc = find_cycle(wait_for_graph(sc))
    steps.append("Re-check: " + ("still deadlocked!" if cyc else "cycle broken, remaining exams can proceed."))
    return steps, sc
