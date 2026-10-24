"""CO1 - System information and OS classification."""
import os
import platform
import sys


def get_system_info():
    """Return a list of (property, value) pairs."""
    info = [
        ("Operating System", f"{platform.system()} {platform.release()}"),
        ("OS Version", platform.version()[:60]),
        ("Machine / Architecture", platform.machine()),
        ("Processor", platform.processor() or "N/A"),
        ("CPU Cores (logical)", str(os.cpu_count())),
        ("Python Version", sys.version.split()[0]),
    ]
    info += _live_info()
    try:
        import psutil
        mem = psutil.virtual_memory()
        info.append(("Total RAM", f"{mem.total / 1024**3:.1f} GB"))
        info.append(("Available RAM", f"{mem.available / 1024**3:.1f} GB"))
    except ImportError:
        pass
    # hide anything that could not be read (shows only real values)
    return [(k, v) for k, v in info if not v.startswith("N/A")]


def _live_info():
    """Hostname, uptime and running process count (psutil optional)."""
    import time
    up, procs = None, None
    try:
        import psutil
        up = time.time() - psutil.boot_time(); procs = len(psutil.pids())
    except ImportError:
        try:
            up = float(open("/proc/uptime").read().split()[0])
            procs = sum(d.isdigit() for d in os.listdir("/proc"))
        except OSError:
            pass
    h = f"{int(up // 3600)}h {int(up % 3600 // 60)}m" if up is not None else "N/A"
    return [("Hostname", platform.node()), ("Uptime", h),
            ("Running Processes", str(procs) if procs is not None else "N/A")]


# (OS service, OS concept, how it appears in this project)
OS_SERVICES = [
    ("Process Management", "Processes, threads, scheduling", "Student sessions = processes, invigilators = threads (CO2, CO3)"),
    ("Resource Management", "Allocation and deadlock", "Hall allocation (FCFS), deadlock on hall + lab (CO3)"),
    ("Memory Management", "Paging, page replacement", "Seating plan pages, LRU for active hall data (CO4)"),
    ("File Management", "Allocation, directories", "Contiguous seating files, tree directory per dept (CO5)"),
    ("Protection / Security", "Access control", "Only the controller can edit seating files; attendance guarded by lock"),
    ("I/O Management", "Device handling", "Answer-sheet collection and attendance entry (simulated)"),
]

BATCH_JUSTIFICATION = """Why exam management is a BATCH PROCESSING scenario
-------------------------------------------------
1. Jobs are submitted together: each exam (department, paper, number of students)
   is a job placed in a queue before the session begins.
2. No interaction while running: once the exam starts, the controller does not
   interact with the job; it simply runs to completion.
3. Jobs run in groups (batches): morning and afternoon sessions are processed
   one batch after another, like a batch OS processing a job queue.
4. Resources are scheduled by the system: halls, invigilators and special rooms
   are allocated automatically (FCFS / Priority) to improve utilisation.
5. Similar jobs are grouped: papers of the same department are handled together
   to reduce set-up time (question paper sets, seating files).

Contrast: an interactive / time-sharing OS would give every student a CPU slice
and respond instantly. Exams do not behave that way, so batch is the best fit."""
