"""Web UI server (standard library only).  Run:  python server.py
Opens http://localhost:8000 - all logic still comes from the co*.py modules."""
import json, queue, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import co1_sysinfo, co2_process, co3_scheduler as sch, co4_memory as mem, co5_files, data

fs = co5_files.build_sample_fs()
sess = {"pcbs": {}, "logs": [], "q": queue.Queue(), "running": False}


def drain():
    while not sess["q"].empty():
        kind, p = sess["q"].get()
        if kind == "pcb":
            sess["pcbs"][p["pid"]] = p
        else:
            sess["logs"].append(p)
            if p.startswith("SESSION COMPLETE"):
                sess["running"] = False


def fs_state():
    def node(n):
        kids = sorted(n.children.values(), key=lambda c: (not c.is_dir, c.name))
        return dict(name=n.name, path=n.path(), dir=n.is_dir,
                    blocks=None if n.is_dir else [n.entry.start, n.entry.length],
                    children=[node(c) for c in kids])
    cells = [None] * fs.disk.n
    for i, e in enumerate(sorted(fs.disk.files.values(), key=lambda e: e.start)):
        for b in range(e.start, e.start + e.length):
            cells[b] = [i, e.path]
    return dict(tree=node(fs.root), disk=cells, stats=fs.disk.stats())


def route(path, q):
    global fs
    g = lambda k, d="": q.get(k, [d])[0]
    if path == "overview":
        rows = sch.fcfs_halls()
        span = max(r["end"] for r in rows if r["end"])
        halls = []
        for h, cap in data.HALLS.items():
            rs = [r for r in rows if r["hall"] == h]
            halls.append(dict(name=h, cap=cap, busy=sum(r["end"] - r["start"] for r in rs),
                              batches=[[r["batch"]["id"], r["batch"]["dept"], r["start"], r["end"], r["batch"]["students"]] for r in rs]))
        return dict(halls=halls, span=span, students=sum(b["students"] for b in data.BATCHES),
                    batches=len(data.BATCHES), invs=[list(i) for i in data.INVIGILATORS])
    if path == "info":
        return dict(info=co1_sysinfo.get_system_info(), services=co1_sysinfo.OS_SERVICES,
                    batch=co1_sysinfo.BATCH_JUSTIFICATION)
    if path == "session/start":
        if sess["running"]:
            return dict(ok=False)
        sess.update(pcbs={}, logs=[], running=True, q=queue.Queue())
        co2_process.start_session(int(g("n", 5)), sess["q"])
        return dict(ok=True)
    if path == "session/poll":
        drain()
        since = int(g("since", 0))
        return dict(pcbs=list(sess["pcbs"].values()), logs=sess["logs"][since:], total=len(sess["logs"]),
                    running=sess["running"], model=co2_process.MULTITHREADING_MODEL)
    if path == "fcfs":
        rows = sch.fcfs_halls()
        return dict(rows=rows, avg=sch.averages(rows))
    if path == "priority":
        res = sch.priority_invigilators(sch.fcfs_halls(), aging=30 if g("aging") == "1" else 0)
        return dict(rows=res, avg=sum(r["wait"] for r in res) / len(res))
    if path == "deadlock":
        sc = sch.DEADLOCK_SCENARIO if g("mode") == "deadlock" else sch.SAFE_SCENARIO
        lines, cyc = sch.detect_deadlock(sc)
        steps = []
        if g("recover") == "1" and cyc:
            steps, sc = sch.recover(sc, cyc)
            lines, cyc = sch.detect_deadlock(sc)
        edges = [[a, b, r] for a, es in sch.wait_for_graph(sc).items() for b, r in es]
        return dict(lines=lines, cycle=cyc, steps=steps, edges=edges, nodes=list(sc["allocation"]))
    if path == "memory":
        ref, n = mem.parse_reference(g("ref", mem.DEFAULT_REFERENCE)), int(g("frames", 3))
        return dict(lru=mem.lru(ref, n), fifo=mem.fifo(ref, n))
    if path.startswith("fs/"):
        op = path[3:]
        if op == "reset":
            fs = co5_files.build_sample_fs()
        elif op == "mkdir":
            fs.mkdir(g("path"))
        elif op == "create":
            fs.create(g("path"), int(g("size")))
        elif op == "delete":
            fs.delete(g("path"))
        elif op == "compact":
            fs.disk.compact()
        return fs_state()
    raise KeyError(path)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.startswith("/api/"):
            try:
                body, code = route(u.path[5:], parse_qs(u.query)), 200
            except Exception as e:          # e.g. DiskFullError -> shown as a toast
                body, code = dict(error=str(e)), 400
            data_ = json.dumps(body).encode()
            ctype = "application/json"
        else:
            data_, code, ctype = (Path(__file__).parent / "index.html").read_bytes(), 200, "text/html; charset=utf-8"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data_)))
        self.end_headers()
        self.wfile.write(data_)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Exam Hall OS Simulator running at http://localhost:8000  (Ctrl+C to stop)")
    threading.Timer(0.8, lambda: webbrowser.open("http://localhost:8000")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
