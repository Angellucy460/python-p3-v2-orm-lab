from __init__ import CONN, CURSOR
from employee import Employee
from department import Department
from faker import Faker
import pytest


class TestEmployee:
    '''Class Employee in employee.py'''

    @pytest.fixture(autouse=True)
    def drop_tables(self):
        '''drop tables prior to each test.'''

        CURSOR.execute("DROP TABLE IF EXISTS employees")
        CURSOR.execute("DROP TABLE IF EXISTS departments")
        CURSOR.execute("DROP TABLE IF EXISTS reviews")
        
        Department.all = {}
        Employee.all = {}
        
    def test_creates_table(self):
        '''contains method "create_table()" that creates table "employees" if it does not exist.'''

        Department.create_table()  # FK constraint requires departments
        Employee.create_table()

        sql = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='employees'
        """
        result = CURSOR.execute(sql).fetchone()
        assert result is not None

    def test_drops_table(self):
        '''contains method "drop_table()" that drops table "employees" if it exists.'''

        Department.create_table()
        Employee.create_table()

        Employee.drop_table()

        # Departments should still exist
        sql = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='departments'
        """
        assert CURSOR.execute(sql).fetchone() is not None

        # Employees should not exist
        sql = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='employees'
        """
        assert CURSOR.execute(sql).fetchone() is None

    def test_saves_employee(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        employee = Employee("Sasha", "Manager", department.id)
        employee.save()

        sql = "SELECT * FROM employees"
        row = CURSOR.execute(sql).fetchone()
        assert (row[0], row[1], row[2], row[3]) == (
            employee.id, employee.name, employee.job_title, employee.department_id
        )

    def test_creates_employee(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        employee = Employee.create("Kai", "Web Developer", department.id)

        row = CURSOR.execute("SELECT * FROM employees").fetchone()
        assert (row[0], row[1], row[2], row[3]) == (
            employee.id, employee.name, employee.job_title, employee.department_id
        )

    def test_instance_from_db(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        CURSOR.execute(
            "INSERT INTO employees (name, job_title, department_id) VALUES (?, ?, ?)",
            ("Amir", "Programmer", department.id)
        )

        row = CURSOR.execute("SELECT * FROM employees").fetchone()
        employee = Employee.instance_from_db(row)

        assert (row[0], row[1], row[2], row[3]) == (
            employee.id, employee.name, employee.job_title, employee.department_id
        )

    def test_finds_by_id(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        faker = Faker()
        employee1 = Employee.create(faker.name(), "Manager", department.id)
        employee2 = Employee.create(faker.name(), "Web Developer", department.id)

        assert Employee.find_by_id(employee1.id).id == employee1.id
        assert Employee.find_by_id(employee2.id).id == employee2.id
        assert Employee.find_by_id(9999) is None

    def test_finds_by_name(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        faker = Faker()
        employee1 = Employee.create(faker.name(), "Manager", department.id)
        employee2 = Employee.create(faker.name(), "Web Developer", department.id)

        assert Employee.find_by_name(employee1.name).id == employee1.id
        assert Employee.find_by_name(employee2.name).id == employee2.id
        assert Employee.find_by_name("Unknown") is None

    def test_updates_row(self):
        Department.create_table()
        department1 = Department("Payroll", "Building A, 5th Floor")
        department1.save()
        department2 = Department("Human Resources", "Building C, 2nd Floor")
        department2.save()

        Employee.create_table()
        employee1 = Employee.create("Raha", "Accountant", department1.id)
        employee2 = Employee.create("Tal", "Benefits Coordinator", department2.id)

        # update Raha
        employee1.name = "Raha Lee"
        employee1.job_title = "Senior Accountant"
        employee1.department_id = department2.id
        employee1.update()

        updated = Employee.find_by_id(employee1.id)
        assert (updated.name, updated.job_title, updated.department_id) == (
            "Raha Lee", "Senior Accountant", department2.id
        )

        not_updated = Employee.find_by_id(employee2.id)
        assert (not_updated.name, not_updated.job_title, not_updated.department_id) == (
            "Tal", "Benefits Coordinator", department2.id
        )

    def test_deletes_row(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        employee1 = Employee.create("Raha", "Accountant", department.id)
        employee2 = Employee.create("Tal", "Benefits Coordinator", department.id)

        employee1.delete()
        assert Employee.find_by_id(employee1.id) is None
        assert employee1.id is None
        assert Employee.all.get(employee1.id) is None

        still_exists = Employee.find_by_id(employee2.id)
        assert still_exists is not None

    def test_gets_all(self):
        Department.create_table()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        Employee.create_table()
        employee1 = Employee.create("Tristan", "Fullstack Developer", department.id)
        employee2 = Employee.create("Sasha", "Manager", department.id)

        employees = Employee.get_all()
        assert len(employees) == 2
        ids = [emp.id for emp in employees]
        assert employee1.id in ids
        assert employee2.id in ids

    def test_get_reviews(self):
        from review import Review  # avoid circular import
        Review.all = {}
        CURSOR.execute("DROP TABLE IF EXISTS reviews")

        Department.create_table()
        department1 = Department.create("Payroll", "Building A, 5th Floor")

        Employee.create_table()
        employee1 = Employee.create("Raha", "Accountant", department1.id)
        employee2 = Employee.create("Tal", "Senior Accountant", department1.id)

        Review.create_table()
        review1 = Review.create(2022, "Good Python coding skills", employee1.id)
        review2 = Review.create(2023, "Great Python coding skills", employee1.id)
        review3 = Review.create(2022, "Good SQL coding skills", employee2.id)

        reviews = employee1.reviews()
        assert len(reviews) == 2
        summaries = [r.summary for r in reviews]
        assert "Good Python coding skills" in summaries
        assert "Great Python coding skills" in summaries
