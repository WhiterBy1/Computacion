import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional, Dict, Any
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, date

# Abstract Student class
class Student(ABC):
    def __init__(self, first_name: str, last_name: str, birth_date: str, student_id: str = None, courses: List[str] = None):
        self._first_name = first_name
        self._last_name = last_name
        self._birth_date = birth_date
        self._student_id = student_id if student_id else str(uuid.uuid4())[:8].upper()
        self._courses = courses if courses else []

    @property
    def first_name(self) -> str:
        return self._first_name

    @first_name.setter
    def first_name(self, value: str) -> None:
        self._first_name = value

    @property
    def last_name(self) -> str:
        return self._last_name

    @last_name.setter
    def last_name(self, value: str) -> None:
        self._last_name = value

    @property
    def full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"

    @property
    def birth_date(self) -> str:
        return self._birth_date

    @birth_date.setter
    def birth_date(self, value: str) -> None:
        self._birth_date = value

    @property
    def student_id(self) -> str:
        return self._student_id

    @property
    def courses(self) -> List[str]:
        return self._courses

    @courses.setter
    def courses(self, value: List[str]) -> None:
        self._courses = value

    @property
    def age(self) -> int:
        try:
            birth_date = datetime.strptime(self._birth_date, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except ValueError:
            return 0

    @property
    def initial(self) -> str:
        return self._first_name[0].upper() if self._first_name else self._last_name[0].upper()

    @abstractmethod
    def display_info(self) -> str:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass

    def add_course(self, course: str) -> None:
        if course not in self._courses:
            self._courses.append(course)

    def remove_course(self, course: str) -> bool:
        if course in self._courses:
            self._courses.remove(course)
            return True
        return False

# Concrete Undergraduate Student class
class UndergraduateStudent(Student):
    def __init__(self, first_name: str, last_name: str, birth_date: str, 
                 major: str, year: int, student_id: str = None, courses: List[str] = None):
        super().__init__(first_name, last_name, birth_date, student_id, courses)
        self._major = major
        self._year = year

    @property
    def major(self) -> str:
        return self._major

    @major.setter
    def major(self, value: str) -> None:
        self._major = value

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        self._year = value

    def display_info(self) -> str:
        year_names = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth"}
        year_str = year_names.get(self._year, f"{self._year}th")
        return f"Undergraduate - {year_str} Year - {self._major}"

    def get_type(self) -> str:
        return "Undergraduate"

# Concrete Graduate Student class
class GraduateStudent(Student):
    def __init__(self, first_name: str, last_name: str, birth_date: str, 
                 program: str, advisor: str, research_topic: str = "", 
                 student_id: str = None, courses: List[str] = None):
        super().__init__(first_name, last_name, birth_date, student_id, courses)
        self._program = program
        self._advisor = advisor
        self._research_topic = research_topic

    @property
    def program(self) -> str:
        return self._program

    @program.setter
    def program(self, value: str) -> None:
        self._program = value

    @property
    def advisor(self) -> str:
        return self._advisor

    @advisor.setter
    def advisor(self, value: str) -> None:
        self._advisor = value

    @property
    def research_topic(self) -> str:
        return self._research_topic

    @research_topic.setter
    def research_topic(self, value: str) -> None:
        self._research_topic = value

    def display_info(self) -> str:
        return f"Graduate - {self._program} - Advisor: {self._advisor}"

    def get_type(self) -> str:
        return "Graduate"

# Validator class
class Validator:
    @staticmethod
    def validate_date_format(date_str: str) -> tuple[bool, str]:
        try:
            if not date_str:
                return False, "Date cannot be empty"
            
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, ""
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes text: removes accents, converts to lowercase, and removes special characters"""
        return re.sub(r'[^\w\s]', '', text.lower()).strip()

# University System class
class UniversitySystem:
    def __init__(self):
        self.students: List[Student] = []
        self.MAX_STUDENTS = 50  # Maximum number of students in the system

    def add_student(self, student: Student) -> bool:
        if len(self.students) >= self.MAX_STUDENTS:
            return False
        
        self.students.append(student)
        return True

    def remove_student(self, student_id: str) -> bool:
        for student in self.students:
            if student.student_id == student_id:
                self.students.remove(student)
                return True
        return False

    def find_student_by_id(self, student_id: str) -> Optional[Student]:
        for student in self.students:
            if student.student_id == student_id:
                return student
        return None

    def search_students(self, query: str) -> List[Student]:
        if not query.strip():
            return sorted(self.students, key=lambda x: x.full_name.lower())

        normalized_query = Validator.normalize_text(query)
        filtered_students = []

        for student in self.students:
            # Search by name
            if normalized_query in Validator.normalize_text(student.full_name):
                filtered_students.append(student)
                continue
            
            # Search by ID
            if normalized_query in student.student_id.lower():
                filtered_students.append(student)
                continue
            
            # Search by courses
            if any(normalized_query in Validator.normalize_text(course) for course in student.courses):
                filtered_students.append(student)
                continue
            
        return sorted(filtered_students, key=lambda x: x.full_name.lower())

    def calculate_average_age(self, student_type: str = None) -> float:
        filtered_students = self.students
        if student_type:
            filtered_students = [s for s in self.students if s.get_type() == student_type]
        
        if not filtered_students:
            return 0
            
        total_age = sum(student.age for student in filtered_students)
        return total_age / len(filtered_students)

    def get_student_count(self, student_type: str = None) -> int:
        if not student_type:
            return len(self.students)
        return sum(1 for student in self.students if student.get_type() == student_type)

# Mock data for testing
sample_students = [
    UndergraduateStudent("John", "Smith", "2002-05-15", "Computer Science", 3, "UG10001", 
                     ["Introduction to Programming", "Data Structures", "Algorithms"]),
    UndergraduateStudent("Emily", "Johnson", "2003-08-22", "Biology", 2, "UG10002",
                     ["Biology 101", "Chemistry", "Laboratory Techniques"]),
    UndergraduateStudent("Michael", "Williams", "2001-03-10", "Mathematics", 4, "UG10003",
                     ["Calculus", "Linear Algebra", "Statistics"]),
    UndergraduateStudent("Jessica", "Brown", "2004-12-03", "Psychology", 1, "UG10004",
                     ["Introduction to Psychology", "Human Development"]),
    UndergraduateStudent("David", "Jones", "2002-07-08", "History", 3, "UG10005",
                     ["World History", "American History", "Research Methods"]),
    GraduateStudent("Robert", "Davis", "1999-02-18", "Ph.D. Computer Science", "Dr. Wilson", 
                "Machine Learning Applications", "GR20001", 
                ["Advanced Algorithms", "Machine Learning", "Research Seminar"]),
    GraduateStudent("Sarah", "Miller", "1998-11-25", "M.Sc. Biology", "Dr. Thompson",
                "Genetic Engineering", "GR20002", 
                ["Advanced Biology", "Research Methods", "Thesis Preparation"]),
    GraduateStudent("James", "Wilson", "1997-09-30", "Ph.D. Physics", "Dr. Martinez",
                "Quantum Computing", "GR20003", 
                ["Quantum Mechanics", "Theoretical Physics", "Research Ethics"]),
    GraduateStudent("Amanda", "Taylor", "1996-04-12", "MBA", "Dr. Anderson",
                "Business Strategy", "GR20004", 
                ["Financial Management", "Strategic Marketing", "Business Ethics"]),
    GraduateStudent("Daniel", "Anderson", "1995-06-07", "M.Sc. Psychology", "Dr. Lewis",
                "Cognitive Behavioral Therapy", "GR20005", 
                ["Advanced Psychology", "Research Methods", "Clinical Practice"]),
]

# Student Form
class StudentForm(tk.Toplevel):
    def __init__(self, parent, university_system: UniversitySystem, on_save: Callable, 
                 student: Optional[Student] = None):
        super().__init__(parent)
        self.title("Edit Student" if student else "New Student")
        self.geometry("500x650")
        self.university_system = university_system
        self.student = student
        self.on_save = on_save
        
        self.setup_form()
        if student:
            self.load_student_data()

    def setup_form(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Student type selection (only shown when creating a new student)
        self.student_type_frame = ttk.LabelFrame(main_frame, text="Student Type", padding=10)
        self.student_type_frame.pack(fill=tk.X, pady=5)
        
        self.student_type = tk.StringVar(value="Undergraduate" if not self.student else 
                                  self.student.get_type())
        ttk.Radiobutton(self.student_type_frame, text="Undergraduate", 
                         variable=self.student_type, value="Undergraduate",
                         command=self.update_form_fields).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(self.student_type_frame, text="Graduate", 
                         variable=self.student_type, value="Graduate",
                         command=self.update_form_fields).pack(side=tk.LEFT, padx=10)
        
        # If editing, disable student type change
        if self.student:
            for child in self.student_type_frame.winfo_children():
                child.configure(state="disabled")
        
        # Basic information section
        self.basic_info_frame = ttk.LabelFrame(main_frame, text="Basic Information", padding=10)
        self.basic_info_frame.pack(fill=tk.X, pady=5)
        
        # Create basic fields with validation
        self.create_labeled_entry(self.basic_info_frame, "First Name:", "first_name", 30)
        self.create_labeled_entry(self.basic_info_frame, "Last Name:", "last_name", 30)
        self.create_labeled_entry(self.basic_info_frame, "Birth Date (YYYY-MM-DD):", "birth_date", 10)
        
        if self.student:
            self.create_labeled_entry(self.basic_info_frame, "Student ID:", "student_id", 8, state="readonly")
        
        # Specific information section (will be populated based on student type)
        self.specific_info_frame = ttk.LabelFrame(main_frame, text="Program Information", padding=10)
        self.specific_info_frame.pack(fill=tk.X, pady=5)
        
        # Courses section
        self.courses_frame = ttk.LabelFrame(main_frame, text="Courses", padding=10)
        self.courses_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.courses_frame, text="Courses (one per line):").pack(anchor=tk.W)
        self.courses_text = tk.Text(self.courses_frame, height=5, width=40)
        self.courses_text.pack(fill=tk.X, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_student).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Update form fields based on initial student type
        self.update_form_fields()

    def update_form_fields(self):
        # Clear specific info frame
        for widget in self.specific_info_frame.winfo_children():
            widget.destroy()
            
        student_type = self.student_type.get()
        
        if student_type == "Undergraduate":
            self.create_labeled_entry(self.specific_info_frame, "Major:", "major", 30)
            
            # Year dropdown
            ttk.Label(self.specific_info_frame, text="Year:").pack(anchor=tk.W)
            self.year_var = tk.IntVar(value=1)
            year_combo = ttk.Combobox(self.specific_info_frame, textvariable=self.year_var, 
                                     values=[1, 2, 3, 4, 5], state="readonly", width=5)
            year_combo.pack(anchor=tk.W, pady=(0, 10))
            
            if self.student and isinstance(self.student, UndergraduateStudent):
                self.major_entry.insert(0, self.student.major)
                self.year_var.set(self.student.year)
                
        elif student_type == "Graduate":
            self.create_labeled_entry(self.specific_info_frame, "Program:", "program", 30)
            self.create_labeled_entry(self.specific_info_frame, "Advisor:", "advisor", 30)
            
            # Research topic
            ttk.Label(self.specific_info_frame, text="Research Topic:").pack(anchor=tk.W)
            self.research_topic_text = tk.Text(self.specific_info_frame, height=3, width=40)
            self.research_topic_text.pack(fill=tk.X, pady=(0, 10))
            
            if self.student and isinstance(self.student, GraduateStudent):
                self.program_entry.insert(0, self.student.program)
                self.advisor_entry.insert(0, self.student.advisor)
                self.research_topic_text.insert("1.0", self.student.research_topic)

    def create_labeled_entry(self, parent, label: str, attr_name: str, max_length: int, **kwargs):
        ttk.Label(parent, text=label).pack(anchor=tk.W)
        
        if kwargs.get("state") == "readonly":
            var = tk.StringVar()
            entry = ttk.Entry(parent, textvariable=var, state="readonly", width=40, **kwargs)
            entry.pack(fill=tk.X, pady=(0, 10))
            setattr(self, f"{attr_name}_var", var)
        else:
            validate_cmd = (self.register(lambda new_text: len(new_text) <= max_length), '%P')
            entry = ttk.Entry(parent, validate="key", validatecommand=validate_cmd, width=40, **kwargs)
            entry.pack(fill=tk.X, pady=(0, 10))
            
        setattr(self, f"{attr_name}_entry", entry)
        return entry

    def load_student_data(self):
        self.first_name_entry.insert(0, self.student.first_name)
        self.last_name_entry.insert(0, self.student.last_name)
        self.birth_date_entry.insert(0, self.student.birth_date)
        
        if hasattr(self, "student_id_var"):
            self.student_id_var.set(self.student.student_id)
            
        self.courses_text.insert("1.0", "\n".join(self.student.courses))

    def get_form_data(self) -> Dict[str, Any]:
        data = {
            'first_name': self.first_name_entry.get().strip(),
            'last_name': self.last_name_entry.get().strip(),
            'birth_date': self.birth_date_entry.get().strip(),
            'courses': [c.strip() for c in self.courses_text.get("1.0", tk.END).split("\n") if c.strip()]
        }
        
        student_type = self.student_type.get()
        
        if student_type == "Undergraduate":
            data.update({
                'major': self.major_entry.get().strip(),
                'year': self.year_var.get()
            })
        else:  # Graduate
            data.update({
                'program': self.program_entry.get().strip(),
                'advisor': self.advisor_entry.get().strip(),
                'research_topic': self.research_topic_text.get("1.0", tk.END).strip()
            })
            
        if self.student:
            data['student_id'] = self.student.student_id
            
        return data

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, str]:
        # Check required fields
        if not data['first_name'] or not data['last_name']:
            return False, "First name and last name are required"
            
        # Validate birth date
        is_valid, error_msg = Validator.validate_date_format(data['birth_date'])
        if not is_valid:
            return False, error_msg
            
        student_type = self.student_type.get()
        
        if student_type == "Undergraduate":
            if not data['major']:
                return False, "Major is required for undergraduate students"
        else:  # Graduate
            if not data['program']:
                return False, "Program is required for graduate students"
            if not data['advisor']:
                return False, "Advisor is required for graduate students"
                
        return True, ""

    def save_student(self):
        data = self.get_form_data()
        
        # Validate data
        is_valid, error_msg = self.validate_data(data)
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return
            
        student_type = self.student_type.get()
        
        try:
            if self.student:  # Update existing student
                # Update basic properties
                self.student.first_name = data['first_name']
                self.student.last_name = data['last_name']
                self.student.birth_date = data['birth_date']
                self.student.courses = data['courses']
                
                if student_type == "Undergraduate" and isinstance(self.student, UndergraduateStudent):
                    self.student.major = data['major']
                    self.student.year = data['year']
                elif student_type == "Graduate" and isinstance(self.student, GraduateStudent):
                    self.student.program = data['program']
                    self.student.advisor = data['advisor']
                    self.student.research_topic = data['research_topic']
                    
                updated_student = self.student
                
            else:  # Create new student
                if student_type == "Undergraduate":
                    new_student = UndergraduateStudent(
                        data['first_name'], 
                        data['last_name'],
                        data['birth_date'],
                        data['major'],
                        data['year'],
                        courses=data['courses']
                    )
                else:  # Graduate
                    new_student = GraduateStudent(
                        data['first_name'], 
                        data['last_name'],
                        data['birth_date'],
                        data['program'],
                        data['advisor'],
                        data['research_topic'],
                        courses=data['courses']
                    )
                    
                if not self.university_system.add_student(new_student):
                    messagebox.showerror("Error", "Maximum number of students reached!")
                    return
                    
                updated_student = new_student
                
            self.on_save(updated_student)
            self.destroy()
            messagebox.showinfo("Success", "Student saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

# University System GUI
class UniversitySystemGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("University Student Management System")
        self.university_system = UniversitySystem()
        self.selected_student = None
        
        self.setup_gui()
        self.load_sample_data()

    def setup_gui(self):
        self.setup_styles()
        self.create_main_layout()
        self.setup_toolbar()
        self.setup_student_list()
        self.setup_details_panel()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Toolbar.TFrame', background='#f0f0f0')
        style.configure('StudentList.TFrame', background='#ffffff')
        style.configure('Details.TFrame', background='#ffffff')
        style.configure('StudentItem.TFrame', background='#ffffff')
        style.configure('StudentItem.Selected.TFrame', background='#e6f2ff')

    def create_main_layout(self):
        # Main content split into left and right panels
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for student list
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        
        # Right panel for student details
        self.right_frame = ttk.Frame(self.paned_window, style='Details.TFrame')
        self.paned_window.add(self.right_frame, weight=2)

    def setup_toolbar(self):
        # Create toolbar at the top of left frame
        self.toolbar = ttk.Frame(self.left_frame, style='Toolbar.TFrame')
        self.toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # Add student button
        self.add_button = ttk.Button(
            self.toolbar, 
            text="Add Student", 
            command=self.add_student
        )
        self.add_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Statistics button
        self.stats_button = ttk.Button(
            self.toolbar,
            text="Statistics",
            command=self.show_statistics
        )
        self.stats_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Search frame below toolbar
        self.search_frame = ttk.Frame(self.left_frame)
        self.search_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search)
        
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill=tk.X, padx=2, pady=2)
        
        # Student type filter
        self.filter_frame = ttk.Frame(self.left_frame)
        self.filter_frame.pack(fill=tk.X, padx=2, pady=2)
        
        self.filter_var = tk.StringVar(value="All")
        ttk.Radiobutton(self.filter_frame, text="All", variable=self.filter_var, 
                       value="All", command=self.refresh_student_list).pack(side=tk.LEFT)
        ttk.Radiobutton(self.filter_frame, text="Undergraduate", variable=self.filter_var,
                       value="Undergraduate", command=self.refresh_student_list).pack(side=tk.LEFT)
        ttk.Radiobutton(self.filter_frame, text="Graduate", variable=self.filter_var,
                       value="Graduate", command=self.refresh_student_list).pack(side=tk.LEFT)

    def setup_student_list(self):
        # Create a canvas with a scrollbar for the student list
        self.list_frame = ttk.Frame(self.left_frame, style='StudentList.TFrame')
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.students_canvas = tk.Canvas(self.list_frame, bg='#ffffff')
        self.students_scrollbar = ttk.Scrollbar(
            self.list_frame, 
            orient=tk.VERTICAL, 
            command=self.students_canvas.yview
        )
        self.students_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.students_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.students_canvas.configure(yscrollcommand=self.students_scrollbar.set)
        
        # Frame to hold student items
        self.students_frame = ttk.Frame(self.students_canvas, style='StudentList.TFrame')
        self.students_canvas_window = self.students_canvas.create_window(
            (0, 0), 
            window=self.students_frame, 
            anchor=tk.NW,
            tags="self.students_frame"
        )
        
        # Configure canvas and frame for scrolling
        self.students_frame.bind("<Configure>", self.on_students_frame_configure)
        self.students_canvas.bind("<Configure>", self.on_students_canvas_configure)
        
        # Handle mouse wheel for scrolling
        self.students_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_students_frame_configure(self, event):
        self.students_canvas.configure(scrollregion=self.students_canvas.bbox("all"))

    def on_students_canvas_configure(self, event):
        self.students_canvas.itemconfig(self.students_canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.students_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_details_panel(self):
        # Student details panel header
        self.details_header = ttk.Frame(self.right_frame)
        self.details_header.pack(fill=tk.X, padx=10, pady=10)
        
        # Student avatar and ID
        self.avatar_frame = ttk.Frame(self.details_header)
        self.avatar_frame.pack(side=tk.LEFT, padx=10)
        
        self.avatar_label = tk.Label(
            self.avatar_frame,
            text="",
            width=3,
            height=2,
            font=('Arial', 14, 'bold'),
            bg='#4285F4',
            fg='white'
        )
        self.avatar_label.pack()
        
        self.student_id_label = ttk.Label(self.avatar_frame, text="", font=('Arial', 10))
        self.student_id_label.pack(pady=(5, 0))
        
        # Student name
        self.name_frame = ttk.Frame(self.details_header)
        self.name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.name_label = ttk.Label(self.name_frame, text="", font=('Arial', 16, 'bold'))
        self.name_label.pack(anchor=tk.W)
        
        self.program_label = ttk.Label(self.name_frame, text="", font=('Arial', 12))
        self.program_label.pack(anchor=tk.W)
        
        # Action buttons
        self.action_frame = ttk.Frame(self.details_header)
        self.action_frame.pack(side=tk.RIGHT, padx=10)
        
        self.edit_button = ttk.Button(
            self.action_frame,
            text="Edit",
            command=self.edit_student
        )
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(
            self.action_frame,
            text="Delete",
            command=self.delete_student
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Student details content
        self.details_content = ttk.Frame(self.right_frame)
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic info section
        self.basic_info = ttk.LabelFrame(self.details_content, text="Basic Information")
        self.basic_info.pack(fill=tk.X, pady=5)
        
        self.basic_info_grid = ttk.Frame(self.basic_info)
        self.basic_info_grid.pack(padx=10, pady=10, fill=tk.X)
        
        # Create basic info fields
        self.create_info_field(self.basic_info_grid, "Birth Date:", 0)
        self.create_info_field(self.basic_info_grid, "Age:", 1)
        
        # Program info section
        self.program_info = ttk.LabelFrame(self.details_content, text="Program Information")
        self.program_info.pack(fill=tk.X, pady=5)
        
        self.program_info_grid = ttk.Frame(self.program_info)
        self.program_info_grid.pack(padx=10, pady=10, fill=tk.X)
        
        # Will be populated based on student type
        
        # Courses section
        self.courses_info = ttk.LabelFrame(self.details_content, text="Courses")
        self.courses_info.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.courses_list = tk.Listbox(self.courses_info)
        self.courses_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initially disable detail buttons
        self.edit_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        
        # Clear details panel
        self.clear_details()

    def create_info_field(self, parent, label_text, row):
        ttk.Label(parent, text=label_text, font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        value_label = ttk.Label(parent, text="", font=('Arial', 10))
        value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        return value_label

    def add_student(self):
        StudentForm(self.root, self.university_system, self.on_student_saved)

    def edit_student(self):
        if not self.selected_student:
            return
        StudentForm(self.root, self.university_system, self.on_student_saved, self.selected_student)

    def delete_student(self):
        if not self.selected_student:
            return
            
        confirmation = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete student {self.selected_student.full_name}?"
        )
        
        if confirmation:
            if self.university_system.remove_student(self.selected_student.student_id):
                messagebox.showinfo("Success", "Student deleted successfully")
                self.refresh_student_list()
                self.clear_details()
                self.selected_student = None
            else:
                messagebox.showerror("Error", "Failed to delete student")

    def show_statistics(self):
        # Create statistics window
        stats_window = tk.Toplevel(self.root)
        stats_window.title("University Statistics")
        stats_window.geometry("400x300")
        stats_window.resizable(False, False)
        
        # Frame for statistics
        stats_frame = ttk.Frame(stats_window, padding=20)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Total students count
        total_students = self.university_system.get_student_count()
        total_undergrad = self.university_system.get_student_count("Undergraduate")
        total_grad = self.university_system.get_student_count("Graduate")
        
        # Average ages
        avg_age_all = round(self.university_system.calculate_average_age(), 1)
        avg_age_undergrad = round(self.university_system.calculate_average_age("Undergraduate"), 1)
        avg_age_grad = round(self.university_system.calculate_average_age("Graduate"), 1)
        
        # Create labels
        ttk.Label(stats_frame, text="University Statistics", font=('Arial', 16, 'bold')).pack(anchor=tk.W, pady=(0, 20))
        
        # Student counts
        counts_frame = ttk.LabelFrame(stats_frame, text="Student Counts")
        counts_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(counts_frame, text=f"Total Students: {total_students}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(counts_frame, text=f"Undergraduate Students: {total_undergrad}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(counts_frame, text=f"Graduate Students: {total_grad}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Average ages
        ages_frame = ttk.LabelFrame(stats_frame, text="Average Ages")
        ages_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ages_frame, text=f"All Students: {avg_age_all} years").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(ages_frame, text=f"Undergraduate Students: {avg_age_undergrad} years").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(ages_frame, text=f"Graduate Students: {avg_age_grad} years").pack(anchor=tk.W, padx=10, pady=2)
        
        # Close button
        ttk.Button(stats_frame, text="Close", command=stats_window.destroy).pack(anchor=tk.E, pady=10)

    def on_student_saved(self, student: Student):
        self.refresh_student_list()
        self.select_student(student)

    def on_search(self, *args):
        self.refresh_student_list()

    def refresh_student_list(self):
        # Clear current list
        for widget in self.students_frame.winfo_children():
            widget.destroy()
            
        # Get search filter
        query = self.search_var.get()
        
        # Get student type filter
        filter_type = None if self.filter_var.get() == "All" else self.filter_var.get()
        
        # Search for students
        students = self.university_system.search_students(query)
        
        # Apply type filter
        if filter_type:
            students = [s for s in students if s.get_type() == filter_type]
            
        # Create student items
        for student in students:
            self.create_student_item(student)
            
        # If previously selected student is not in the filtered list, clear selection
        if self.selected_student and self.selected_student not in students:
            self.clear_details()
            self.selected_student = None

    def create_student_item(self, student: Student):
        # Create frame for student item
        item_frame = ttk.Frame(self.students_frame, style='StudentItem.TFrame')
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Add avatar
        avatar_label = tk.Label(
            item_frame,
            text=student.initial,
            width=2,
            height=1,
            font=('Arial', 14, 'bold'),
            bg='#4285F4',
            fg='white'
        )
        avatar_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Add student info
        info_frame = ttk.Frame(item_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        name_label = ttk.Label(
            info_frame,
            text=student.full_name,
            font=('Arial', 12)
        )
        name_label.pack(anchor=tk.W)
        
        id_label = ttk.Label(
            info_frame,
            text=f"ID: {student.student_id}",
            font=('Arial', 10)
        )
        id_label.pack(anchor=tk.W)
        
        # Add program info
        program_label = ttk.Label(
            info_frame,
            text=student.display_info(),
            font=('Arial', 10)
        )
        program_label.pack(anchor=tk.W)
        
        # Handle click event
        for widget in [item_frame, avatar_label, info_frame, name_label, id_label, program_label]:
            widget.bind("<Button-1>", lambda e, s=student: self.select_student(s))
            
        # If this is the selected student, highlight it
        if self.selected_student and self.selected_student.student_id == student.student_id:
            item_frame.configure(style='StudentItem.Selected.TFrame')
            
        return item_frame

    def select_student(self, student: Student):
        self.selected_student = student
        
        # Update details panel
        self.update_details(student)
        
        # Refresh list to highlight selected item
        self.refresh_student_list()
        
        # Enable action buttons
        self.edit_button.configure(state="normal")
        self.delete_button.configure(state="normal")

    def update_details(self, student: Student):
        # Update avatar
        self.avatar_label.configure(text=student.initial)
        
        # Update student ID
        self.student_id_label.configure(text=f"ID: {student.student_id}")
        
        # Update name
        self.name_label.configure(text=student.full_name)
        
        # Update program info
        self.program_label.configure(text=student.display_info())
        
        # Clear previous info
        for widget in self.basic_info_grid.winfo_children():
            widget.destroy()
            
        for widget in self.program_info_grid.winfo_children():
            widget.destroy()
            
        self.courses_list.delete(0, tk.END)
        
        # Add basic info
        birth_label = self.create_info_field(self.basic_info_grid, "Birth Date:", 0)
        birth_label.configure(text=student.birth_date)
        
        age_label = self.create_info_field(self.basic_info_grid, "Age:", 1)
        age_label.configure(text=f"{student.age} years")
        
        # Add specific info based on student type
        if isinstance(student, UndergraduateStudent):
            major_label = self.create_info_field(self.program_info_grid, "Major:", 0)
            major_label.configure(text=student.major)
            
            year_label = self.create_info_field(self.program_info_grid, "Year:", 1)
            year_names = {1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth"}
            year_str = year_names.get(student.year, f"{student.year}th")
            year_label.configure(text=year_str)
            
        elif isinstance(student, GraduateStudent):
            program_label = self.create_info_field(self.program_info_grid, "Program:", 0)
            program_label.configure(text=student.program)
            
            advisor_label = self.create_info_field(self.program_info_grid, "Advisor:", 1)
            advisor_label.configure(text=student.advisor)
            
            if student.research_topic:
                research_frame = ttk.Frame(self.program_info)
                research_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
                
                ttk.Label(research_frame, text="Research Topic:", 
                         font=('Arial', 10, 'bold')).pack(anchor=tk.W)
                         
                topic_text = tk.Text(research_frame, height=3, wrap=tk.WORD)
                topic_text.pack(fill=tk.X, pady=(2, 0))
                topic_text.insert("1.0", student.research_topic)
                topic_text.configure(state="disabled")
        
        # Add courses
        for course in student.courses:
            self.courses_list.insert(tk.END, course)

    def clear_details(self):
        # Clear avatar
        self.avatar_label.configure(text="")
        
        # Clear student ID
        self.student_id_label.configure(text="")
        
        # Clear name
        self.name_label.configure(text="")
        
        # Clear program info
        self.program_label.configure(text="")
        
        # Clear basic info
        for widget in self.basic_info_grid.winfo_children():
            widget.destroy()
            
        # Clear program info
        for widget in self.program_info_grid.winfo_children():
            widget.destroy()
        
        # Remove any research topic text area
        for widget in self.program_info.winfo_children():
            if widget != self.program_info_grid:
                widget.destroy()
                
        # Clear courses
        self.courses_list.delete(0, tk.END)
        
        # Disable action buttons
        self.edit_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")

    def load_sample_data(self):
        # Add sample students to university system
        for student in sample_students:
            self.university_system.add_student(student)
            
        # Refresh the student list
        self.refresh_student_list()


def main():
    root = tk.Tk()
    root.title("University Student Management System")
    root.geometry("1000x700")
    root.minsize(900, 600)
    
    app = UniversitySystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()