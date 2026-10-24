# College Exam Hall Management System

**An Operating System simulator that uses a college exam event as its scenario.**

Subject: Operating System (315319) | Project-5 | Class: CO5K
Vidyalankar Polytechnic, Computer Engineering

Student: YOUR NAME | Roll No: YOUR ROLL NO

---

## 1. About the project

Running a big examination needs many shared resources at the same time: exam halls, invigilators, seating data and the files that store seating plans. If this is done by hand, halls sit idle, students wait for a long time, and clashes happen when two exams each hold something the other one needs.

This project simulates how an **operating system** manages such resources. Every exam idea is mapped to an OS idea:

| Exam event | OS concept |
|---|---|
| Student's exam session | Process |
| Invigilator | Thread |
| Hall allocation | FCFS scheduling |
| Invigilator assignment | Priority scheduling |
| Hall and lab clash | Deadlock |
| Seating plan | Memory pages |
| Seating files | Contiguous file allocation |

The project is a **web dashboard** that runs on your own computer. Nothing is sent over the internet.

---

## 2. Course outcomes covered

| CO | Requirement | Where it is done |
|---|---|---|
| CO1 | Show system info; classify exam management as a batch processing OS scenario | `co1_sysinfo.py` |
| CO2 | Student session = process, invigilator = thread, show multithreading model | `co2_process.py` |
| CO3 | Hall allocation with FCFS, invigilators with Priority, hall-resource deadlock detection | `co3_scheduler.py` |
| CO4 | Seating plan in memory pages, LRU to manage active hall data | `co4_memory.py` |
| CO5 | Seating files with contiguous allocation, tree-structured directory per department | `co5_files.py` |

---

## 3. How to run

**Requirements**

- Python 3 (tested on Python 3.14, Windows 11)
- A web browser
- No `pip install` is needed. The `psutil` library is optional (only for extra system info such as RAM).

**Steps**

1. Download the project: click **Code**, then **Download ZIP**, and extract it. Or use Git:
   ```
   git clone https://github.com/YOUR-USERNAME/exam-hall-os-simulator.git
   ```
2. Open a terminal in the project folder.
3. Run:
   ```
   python main.py
   ```
4. The browser opens at **http://localhost:8000**. If it does not open, type that address yourself.
5. Press **Ctrl + C** in the terminal to stop the server.

The server listens on `127.0.0.1` only, so nobody else on the network can reach it.

---

## 4. Technology used

- **Python 3 standard library only:** `threading`, `queue`, `collections`, `heapq`, `http.server` for the logic and the server.
- **HTML, CSS and JavaScript** (one file, no external libraries) for the dashboard.

---

## 5. Architecture (three layers)

```
 Browser (index.html)          <- Interface layer: tables, Gantt charts, animations
        |  JSON over HTTP (GET)
 server.py (ThreadingHTTPServer)  <- Server layer: calls the logic, returns JSON
        |
 co1 ... co5 + data.py          <- Simulation layer: the real OS logic
```

`main.py` only starts the server and opens the browser.

---

## 6. Project structure

```
exam-hall-os-simulator/
├── main.py             Starts the server
├── server.py           Local web server
├── data.py             Sample data (halls, batches, invigilators, students)
├── co1_sysinfo.py      CO1: system info, OS services, batch justification
├── co2_process.py      CO2: PCB, student processes, invigilator threads
├── co3_scheduler.py    CO3: FCFS, Priority, deadlock detection and recovery
├── co4_memory.py       CO4: paging, LRU and FIFO page replacement
├── co5_files.py        CO5: disk, contiguous allocation, tree directory
├── index.html          The dashboard (all pages in one file)
└── README.md
```

---

## 7. Sample data

Sample data is loaded automatically, so every page works as soon as you start the program.

**Halls**

| Hall | Seats |
|---|---|
| Hall A | 60 |
| Hall B | 40 |
| Hall C | 80 |
| Hall D | 30 |

**Exam batches** (times in minutes, priority 1 = most important)

| Batch | Dept | Students | Arrival | Duration | Priority |
|---|---|---|---|---|---|
| B1 | CSE | 55 | 0 | 60 | 2 |
| B2 | ECE | 35 | 5 | 90 | 1 |
| B3 | MECH | 70 | 10 | 60 | 3 |
| B4 | CSE | 28 | 15 | 45 | 1 |
| B5 | ECE | 60 | 20 | 60 | 2 |
| B6 | MECH | 40 | 25 | 90 | 3 |
| B7 | CIVIL | 30 | 30 | 60 | 2 |

**Invigilators:** Prof. Rao (rank 1), Dr. Iyer (rank 2), Mr. Khan (rank 3).

---

## 8. Module details

### Module 1: System and batch processing (CO1)

- Explains the OS services used in the project: process, resource, memory, file, protection and I/O management.
- Justifies **batch processing**: exams are submitted as a queue of jobs, run without interaction, and are processed in sessions. A time-sharing system does not fit this pattern.
- System information (OS, CPU cores and so on) is collected and used in the dashboard pipeline.

### Module 2: Process management (CO2)

- Each student's exam session is a **process** with a **Process Control Block (PCB)**: PID, name, roll number, state, hall, seat and start time.
- Process states: `New`, `Ready`, `Running`, `Waiting`, `Terminated`.
- Each hall has **one invigilator thread** that supervises all the students in that hall. This is the **one-to-many** model.
- Python threads map one-to-one to kernel threads on the host OS.
- A `threading.Lock` protects the shared attendance sheet, so two threads cannot update it at the same time (the critical section problem).
- Threads send their events to the dashboard through a `queue.Queue`.
- Some students ask for an extra answer sheet, which shows the `Waiting` (I/O wait) state.

### Module 3: Scheduling and deadlock (CO3)

**FCFS hall allocation**
- Batches are served in order of arrival.
- Each batch takes the hall that fits its students and lets it start earliest. If two halls tie, the smaller hall is used.
- Reports start, end, waiting time and turnaround time, and draws a Gantt chart.
- Weakness: the **convoy effect**, where a large exam holds a hall while others wait.

**Priority invigilator assignment**
- Uses a min-heap (`heapq`). Lower number = higher priority.
- The most senior free invigilator takes the highest-priority waiting exam.
- It is non-preemptive.
- Optional **aging**: every 30 minutes of waiting improves the priority by 1, so low-priority exams do not starve.

**Deadlock detection and recovery**
- Halls, labs and a projector are the resources.
- A **wait-for graph** is built and a depth-first search finds a cycle.
- Recovery: the exam with the lowest priority in the cycle is chosen as the **victim**. Its resources are released, it is rescheduled, and the graph is checked again.
- A safe scenario (no cycle) is also included for comparison.

### Module 4: Memory management (CO4)

- Each hall's seating plan is split into **pages of 10 seats**. For example, page `A2` means Hall A, seats 21 to 30.
- Memory holds only a fixed number of **frames**. When a page is missing (a **page fault**) and memory is full, **LRU** removes the least recently used page.
- **FIFO** is included for comparison.
- The page shows every step, the frame contents, the evicted page, hits, faults and the hit ratio.
- Default reference string: `A0 B0 A0 C0 A0 B0 D0 A0 B0 C0 A0 B0 A1 A0 B0 D0`

### Module 5: File management (CO5)

- A simulated disk of **100 blocks** with a bitmap of used and free blocks.
- Seating files use **contiguous allocation** with **first-fit**.
- Files are stored in a **tree-structured directory**: one folder per department, then one per semester.
- Operations: `mkdir`, `create file`, `delete`, `compact disk`, `reset`.
- Shows used blocks, free blocks, the largest hole and **external fragmentation**. Compaction moves the files together and removes the fragmentation.
- The sample disk starts with a 7-block hole in the middle, so fragmentation is visible at once.

---

## 9. Dashboard pages

| Page | What it shows |
|---|---|
| Dashboard | Summary cards (students, batches, halls, invigilators), hall plan with busy %, OS pipeline with a **Run all modules** button |
| System & Batch | OS services table and the batch processing justification |
| Processes | Live PCB table with coloured state pills, state counters and the invigilator thread log |
| Scheduling | FCFS table and Gantt chart, Priority table and Gantt chart (aging checkbox), deadlock graph with **Recover** and **Safe scenario** buttons |
| Memory | Frames and reference string inputs, LRU or FIFO choice, hit ratio bars, step-by-step table |
| File System | Clickable directory tree, 100-block disk grid, buttons for all file operations, and disk statistics |

---

## 10. Expected results with the sample data

| Module | Result |
|---|---|
| FCFS | Average waiting time about **16.4 min**, average turnaround about **82.9 min**. B5, B6 and B7 wait 40, 45 and 30 minutes. |
| Priority | Average invigilator wait about **17.9 min**. With aging on, the result is the same for this sample data. |
| Deadlock | Cycle **Exam-A -> Exam-B -> Exam-A**. Exam-B is chosen as the victim. After recovery the cycle is gone. Exam-C is only blocked, not deadlocked. |
| Memory (3 frames) | LRU: 9 hits, 7 faults (**56.3%**). FIFO: 5 hits, 11 faults (**31.3%**). |
| Memory (5 frames) | LRU and FIFO both: 11 hits, 5 faults (**68.8%**). All 5 pages fit, so nothing is replaced. |
| Files | **61 of 100** blocks used, about **18%** external fragmentation. After compaction: 0%. |

---

## 11. Limitations and future scope

- FCFS causes the convoy effect, and priority scheduling can starve low-priority jobs without aging.
- Contiguous allocation cannot grow a file in place. Linked or indexed allocation would avoid this.
- The deadlock demo uses a fixed scenario, not one built from the live hall allocation.
- The simulation uses fixed sample data. A future version could read real student and hall data from a database.

---

## 12. Conclusion

The project shows that OS techniques can run an exam event efficiently. FCFS gives a simple and fair hall allocation but small exams may wait behind large ones. Priority scheduling gives important exams the senior invigilators, and aging prevents starvation. Wait-for graphs detect deadlock, and preempting a victim recovers from it. LRU gave a higher hit ratio than FIFO when memory was small. Contiguous allocation is fast to access but suffers from external fragmentation, which compaction fixes.

---

*Made for the Operating System project, Vidyalankar Polytechnic, 2026-27.*
