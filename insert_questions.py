import sqlite3

conn = sqlite3.connect("exam.db")
cursor = conn.cursor()

questions = [
    ("What does the 'ls' command do in Linux?", "List files", "Delete files", "Copy files", "Move files", "A"),
    ("Which data structure uses FIFO (First In First Out)?", "Stack", "Queue", "Tree", "Graph", "B"),
    ("Which keyword is used to define a function in Python?", "func", "def", "function", "lambda", "B"),
    ("Which protocol is used for secure communication over the internet?", "HTTP", "FTP", "HTTPS", "SMTP", "C"),
    ("Which of the following is a relational database?", "MongoDB", "MySQL", "Redis", "Neo4j", "B"),
    ("What does HTML stand for?", "HyperText Markup Language", "HighText Machine Language", "Hyperlink Text Management Language", "None", "A"),
    ("Which symbol is used for comments in Python?", "#", "//", "/* */", "--", "A"),
    ("Which OS is developed by Apple?", "Windows", "Linux", "macOS", "Android", "C"),
    ("Which sorting algorithm is fastest on average?", "Bubble Sort", "Quick Sort", "Insertion Sort", "Selection Sort", "B"),
    ("Which keyword is used to exit a loop in Python?", "stop", "exit", "break", "quit", "C"),
    ("Which layer of OSI handles routing?", "Transport", "Network", "Data Link", "Application", "B"),
    ("Which file extension is used for Python files?", ".java", ".py", ".cpp", ".exe", "B"),
    ("Which company created Java?", "Microsoft", "Sun Microsystems", "Google", "IBM", "B"),
    ("Which protocol is used for email?", "SMTP", "HTTP", "FTP", "SSH", "A"),
    ("Which keyword is used to create a class in Python?", "class", "def", "struct", "object", "A"),
    ("Which operator is used for exponentiation in Python?", "^", "**", "exp()", "//", "B"),
    ("Which device is used to connect networks?", "Switch", "Router", "Hub", "Repeater", "B"),
    ("Which data type is immutable in Python?", "List", "Dictionary", "Tuple", "Set", "C"),
    ("Which algorithm is used in Dijkstra’s shortest path?", "Greedy", "Dynamic Programming", "Divide & Conquer", "Backtracking", "A"),
    ("Which keyword is used to import modules in Python?", "include", "import", "require", "module", "B"),
    ("Which tag is used for headings in HTML?", "<h1>", "<head>", "<title>", "<p>", "A"),
    ("Which SQL command is used to remove a table?", "DELETE", "DROP", "REMOVE", "CLEAR", "B"),
    ("Which protocol secures websites?", "HTTP", "HTTPS", "FTP", "SSH", "B"),
    ("Which keyword is used to handle exceptions in Python?", "catch", "try", "except", "error", "C"),
    ("Which algorithm is used for searching in sorted arrays?", "Linear Search", "Binary Search", "DFS", "BFS", "B"),
    ("Which company created Windows?", "Apple", "Microsoft", "Google", "IBM", "B"),
    ("Which keyword is used to continue loop execution?", "skip", "next", "continue", "pass", "C"),
    ("Which HTML tag is used for links?", "<a>", "<link>", "<href>", "<url>", "A"),
    ("Which keyword is used to define constants in Python?", "const", "final", "None", "No keyword", "D"),
    ("Which algorithm is used in RSA encryption?", "Prime factorization", "Sorting", "Hashing", "Greedy", "A"),
]

cursor.executemany("""
INSERT INTO questions (text, option_a, option_b, option_c, option_d, correct_option)
VALUES (?, ?, ?, ?, ?, ?)
""", questions)

conn.commit()
conn.close()

print("30 sample questions inserted successfully!")
