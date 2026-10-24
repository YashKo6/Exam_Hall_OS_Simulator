"""CO2 - Student sessions as processes, invigilators as threads."""
import itertools
import queue
import random
import threading
import time

import data

STATES = ["New", "Ready", "Running", "Waiting", "Terminated"]

MULTITHREADING_MODEL = (
    "Multithreading model: ONE-TO-MANY (user-level view)\n"
    "- Each hall has ONE invigilator thread.\n"
    "- That thread supervises MANY student processes in the hall.\n"
    "- Threads share the process memory (attendance sheet), so a Lock guards updates.\n"
    "- Python threads map ONE-TO-ONE to kernel threads on the host OS."
)

_pid_counter = itertools.count(1001)


class PCB:
    """Process Control Block for one student's exam session."""

    def __init__(self, name, roll, hall, seat, priority=2, duration=60):
        self.pid = next(_pid_counter)
        self.name = name
        self.roll = roll
        self.hall = hall
        self.seat = seat
        self.priority = priority
        self.duration = duration
        self.state = "New"
        self.start_time = None

    def snapshot(self):
        return dict(pid=self.pid, name=self.name, roll=self.roll, state=self.state,
                    hall=self.hall, seat=self.seat,
                    start=time.strftime("%H:%M:%S", time.localtime(self.start_time)) if self.start_time else "-")


def create_students(per_hall, halls=None):
    halls = halls or list(data.HALLS)
    result = {}
    n = 0
    for h in halls:
        result[h] = []
        for seat in range(1, per_hall + 1):
            name = data.STUDENT_NAMES[n % len(data.STUDENT_NAMES)]
            result[h].append(PCB(name, f"R{n + 1:03d}", h, seat))
            n += 1
    return result


class Invigilator(threading.Thread):
    def __init__(self, name, hall, students, attendance, lock, out_q, delay):
        super().__init__(name=name, daemon=True)
        self.hall, self.students = hall, students
        self.attendance, self.lock, self.out_q, self.delay = attendance, lock, out_q, delay

    def emit(self, pcb):
        self.out_q.put(("pcb", pcb.snapshot()))

    def log(self, msg):
        self.out_q.put(("log", f"[{self.name} | {self.hall}] {msg}"))

    def run(self):
        self.log(f"thread started, supervising {len(self.students)} student processes")
        for s in self.students:                       # New -> Ready (admitted)
            s.state = "Ready"; self.emit(s); time.sleep(self.delay / 3)
        for s in self.students:                       # Ready -> Running (attendance)
            with self.lock:                           # critical section
                self.attendance[self.hall] = self.attendance.get(self.hall, 0) + 1
            s.state = "Running"; s.start_time = time.time(); self.emit(s)
            self.log(f"{s.name} (PID {s.pid}) seated at {s.seat}, attendance marked")
            time.sleep(self.delay / 3)
        time.sleep(self.delay)
        for s in self.students:                       # some students ask for extra sheets
            if random.random() < 0.3:
                s.state = "Waiting"; self.emit(s)
                self.log(f"{s.name} waiting for extra answer sheet (I/O wait)")
                time.sleep(self.delay); s.state = "Running"; self.emit(s)
        time.sleep(self.delay)
        for s in self.students:                       # Running -> Terminated
            s.state = "Terminated"; self.emit(s); time.sleep(self.delay / 3)
        self.log("all students submitted, thread finished")


def start_session(per_hall, out_q, delay=0.4):
    """Create PCBs + one invigilator thread per hall. Returns (students_by_hall, threads)."""
    students = create_students(per_hall)
    attendance, lock = {}, threading.Lock()
    invs = [n for n, _ in data.INVIGILATORS]
    threads = []
    for i, (hall, plist) in enumerate(students.items()):
        for p in plist:
            out_q.put(("pcb", p.snapshot()))
        t = Invigilator(invs[i % len(invs)] if i < len(invs) else f"Invig-{i + 1}",
                        hall, plist, attendance, lock, out_q, delay)
        threads.append(t)
    for t in threads:
        t.start()

    def monitor():
        for t in threads:
            t.join()
        out_q.put(("log", f"SESSION COMPLETE. Attendance sheet: {attendance}"))
    threading.Thread(target=monitor, daemon=True).start()
    return students, threads
