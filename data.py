"""Sample data shared by all modules."""

# Hall name -> seating capacity
HALLS = {"Hall A": 60, "Hall B": 40, "Hall C": 80, "Hall D": 30}

# Exam batches (jobs). Times are in minutes from the start of the session.
# priority: 1 = most important (used for invigilator assignment)
BATCHES = [
    dict(id="B1", dept="CSE",   paper="Data Structures", students=55, arrival=0,  duration=60, priority=2),
    dict(id="B2", dept="ECE",   paper="Signals",         students=35, arrival=5,  duration=90, priority=1),
    dict(id="B3", dept="MECH",  paper="Thermodynamics",  students=70, arrival=10, duration=60, priority=3),
    dict(id="B4", dept="CSE",   paper="Operating Sys",   students=28, arrival=15, duration=45, priority=1),
    dict(id="B5", dept="ECE",   paper="VLSI",            students=60, arrival=20, duration=60, priority=2),
    dict(id="B6", dept="MECH",  paper="Fluid Mechanics", students=40, arrival=25, duration=90, priority=3),
    dict(id="B7", dept="CIVIL", paper="Structures",      students=30, arrival=30, duration=60, priority=2),
]

# (name, rank) - rank 1 = most senior (Professor), 2 = Lecturer, 3 = Teaching Assistant
INVIGILATORS = [("Prof. Rao", 1), ("Dr. Iyer", 2), ("Mr. Khan", 3)]

STUDENT_NAMES = [
    "Aarav", "Diya", "Rohan", "Sneha", "Kabir", "Ananya", "Vikram", "Meera",
    "Arjun", "Isha", "Neel", "Pooja", "Rahul", "Tanvi", "Yash", "Riya",
    "Karan", "Sara", "Dev", "Nisha",
]
