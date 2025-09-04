from __init__ import CONN, CURSOR
from department import Department


class Employee:
    all = {}

    def __init__(self, name, job_title, department_id, id=None):
        self.id = id
        self.name = name
        self.job_title = job_title
        self.department_id = department_id

    def __repr__(self):
        return f"<Employee {self.id}: {self.name}, {self.job_title}, Dept {self.department_id}>"

    # =========================
    # Property: name
    # =========================
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Employee name must be a string")
        if len(value.strip()) == 0:
            raise ValueError("Employee name must be a non-empty string")
        self._name = value

    # =========================
    # Property: job_title
    # =========================
    @property
    def job_title(self):
        return self._job_title

    @job_title.setter
    def job_title(self, value):
        if not isinstance(value, str):
            raise ValueError("Job title must be a string")
        if len(value.strip()) == 0:
            raise ValueError("Job title must be a non-empty string")
        self._job_title = value

    # =========================
    # Property: department_id (FK)
    # =========================
    @property
    def department_id(self):
        return self._department_id

    @department_id.setter
    def department_id(self, value):
        if not isinstance(value, int):
            raise ValueError("Department ID must be an integer")
        if value not in Department.all:
            raise ValueError("Department ID must reference an existing Department")
        self._department_id = value

    # =========================
    # Table methods
    # =========================
    @classmethod
    def create_table(cls):
        sql = """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                job_title TEXT,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        sql = "DROP TABLE IF EXISTS employees"
        CURSOR.execute(sql)
        CONN.commit()

    # =========================
    # Persistence methods
    # =========================
    def save(self):
        if self.id is None:
            sql = """
                INSERT INTO employees (name, job_title, department_id)
                VALUES (?, ?, ?)
            """
            CURSOR.execute(sql, (self.name, self.job_title, self.department_id))
            CONN.commit()
            self.id = CURSOR.lastrowid
            Employee.all[self.id] = self
        else:
            self.update()

    @classmethod
    def create(cls, name, job_title, department_id):
        employee = cls(name, job_title, department_id)
        employee.save()
        return employee

    @classmethod
    def instance_from_db(cls, row):
        emp_id, name, job_title, department_id = row
        if emp_id in cls.all:
            emp = cls.all[emp_id]
            emp.name = name
            emp.job_title = job_title
            emp.department_id = department_id
        else:
            emp = cls(name, job_title, department_id, emp_id)
            cls.all[emp_id] = emp
        return emp

    @classmethod
    def find_by_id(cls, emp_id):
        sql = "SELECT * FROM employees WHERE id = ?"
        row = CURSOR.execute(sql, (emp_id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def find_by_name(cls, name):
        sql = "SELECT * FROM employees WHERE name = ?"
        row = CURSOR.execute(sql, (name,)).fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def get_all(cls):
        sql = "SELECT * FROM employees"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]

    def update(self):
        sql = """
            UPDATE employees
            SET name = ?, job_title = ?, department_id = ?
            WHERE id = ?
        """
        CURSOR.execute(sql, (self.name, self.job_title, self.department_id, self.id))
        CONN.commit()

    def delete(self):
        sql = "DELETE FROM employees WHERE id = ?"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()
        del Employee.all[self.id]
        self.id = None

    # =========================
    # Relationship: Reviews
    # =========================
    def reviews(self):
        from review import Review  # avoid circular import
        sql = "SELECT * FROM reviews WHERE employee_id = ?"
        rows = CURSOR.execute(sql, (self.id,)).fetchall()
        return [Review.instance_from_db(row) for row in rows]
