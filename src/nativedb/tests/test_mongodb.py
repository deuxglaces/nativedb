import datetime
import unittest

import pymongo

import nativedb.mongodb


class TestMongoDb(unittest.TestCase):
    def tearDown(self) -> None:
        pymongo.MongoClient().drop_database('NativeDbTest')

    def test_001_new(self):
        @nativedb.database('NativeDbTest')
        class Employee(nativedb.mongodb.MongoDbModel):
            employee_id: nativedb.Unique[str]
            name: str
            dob: datetime.date

        @nativedb.database('NativeDbTest')
        class Department(nativedb.mongodb.MongoDbModel):
            department_code: nativedb.Unique[str]
            name: nativedb.Unique[str]
            employees: list[Employee]

        self.assertEqual(0, len(Employee.all()))
        self.assertEqual(0, len(Department.all()))
        test_employee = Employee(
            employee_id='NewEmployeeId',
            name='Deux Glaces',
            dob=datetime.date(1999, 12, 31),
        )

        test_department = Department(
            department_code='Weirdoes',
            name='Pythonistas!',
            employees=[test_employee],
        )

        self.assertEqual('NewEmployeeId', test_employee.employee_id)
        self.assertEqual('Deux Glaces', test_employee.name)
        self.assertEqual(datetime.date(1999, 12, 31), test_employee.dob)

        self.assertEqual('Weirdoes', test_department.department_code)
        self.assertEqual('Pythonistas!', test_department.name)
        self.assertEqual([test_employee], test_department.employees)
        self.assertIs(test_employee, test_department.employees[0])

        self.assertEqual(1, len(Employee.all()))
        retrieved_employee = Employee.find_one()
        self.assertIs(test_employee, retrieved_employee)
        self.assertEqual(datetime.date(1999, 12, 31), retrieved_employee.dob)

        del test_employee
        del test_department
        retrieved_employee = Employee.find_one()
        retrieved_dept = Department.find_one()
        self.assertEqual(datetime.date(1999, 12, 31), retrieved_employee.dob)
        self.assertIs(retrieved_dept.employees[0], retrieved_employee)

    def test_002_update_and_save(self):
        @nativedb.database('NativeDbTest')
        class Employee(nativedb.mongodb.MongoDbModel):
            employee_id: nativedb.Unique[str]
            name: nativedb.NotNull[str]
            dob: datetime.date

        @nativedb.database('NativeDbTest')
        class Department(nativedb.mongodb.MongoDbModel):
            department_code: nativedb.Unique[str]
            name: nativedb.Unique[str]
            employees: list[Employee]

        self.assertEqual(0, len(Employee.all()))
        self.assertEqual(0, len(Department.all()))
        test_employee = Employee(
            employee_id='NewEmployeeId',
            name='Deux Glaces',
            dob=datetime.date(1999, 12, 31),
        )

        self.assertEqual('NewEmployeeId', test_employee.employee_id)
        self.assertEqual('Deux Glaces', test_employee.name)
        self.assertEqual(datetime.date(1999, 12, 31), test_employee.dob)

        self.assertEqual(1, len(Employee.all()))
        retrieved_employee = Employee.find_one()
        self.assertIs(test_employee, retrieved_employee)
        self.assertEqual(datetime.date(1999, 12, 31), retrieved_employee.dob)

        # update changes a single object, and all references will be updated at once
        retrieved_employee.update(name='Dooo Glaces')
        self.assertEqual('Dooo Glaces', test_employee.name)
        self.assertEqual('Dooo Glaces', retrieved_employee.name)

        # update with no args does nothing
        retrieved_employee.update()
        del test_employee
        retrieved_employee = Employee.find_one()
        self.assertEqual('Dooo Glaces', retrieved_employee.name)

        # save updates database after changing instance
        retrieved_employee.name = 'Deux Glaces'
        retrieved_employee.save()
        self.assertEqual('Deux Glaces', retrieved_employee.name)
        del retrieved_employee
        retrieved_employee = Employee.find_one()
        self.assertEqual('Deux Glaces', retrieved_employee.name)

        # save updates kwargs too
        retrieved_employee.name = 'Pi Thagoras'
        retrieved_employee.save(dob=datetime.date(2020, 3, 14))
        del retrieved_employee
        retrieved_employee = Employee.find_one()
        self.assertEqual('Pi Thagoras', retrieved_employee.name)
        self.assertEqual(datetime.date(2020, 3, 14), retrieved_employee.dob)

        # update only updates the kwargs, not the other fields
        retrieved_employee.name = 'Don\'t name your child this'
        retrieved_employee.update(dob=datetime.date(2020, 12, 25))
        del retrieved_employee
        retrieved_employee = Employee.find_one()
        self.assertEqual('Pi Thagoras', retrieved_employee.name)
        self.assertEqual(datetime.date(2020, 12, 25), retrieved_employee.dob)

        # update a unique field to a value that is already present in a different document
        new_employee = Employee(
            employee_id='StanEmployeeId',
            name='Old Timer',
            dob=datetime.date(1921, 1, 1)
        )
        self.assertRaises(
            nativedb.exceptions.UniqueConflict,
            new_employee.update,
            employee_id='NewEmployeeId',
        )
        # but different value doesn't raise the exception
        new_employee.update(employee_id='DifferentEmployeeId')
        new_employee.delete()

    def test_901_test_config(self):
        nativedb.mongodb_config(database='NativeDbTest')

        class Employee(nativedb.mongodb.MongoDbModel):
            employee_id: nativedb.Unique[str]
            name: str
            dob: datetime.date

        class Department(nativedb.mongodb.MongoDbModel):
            department_code: nativedb.Unique[str]
            name: nativedb.Unique[str]
            employees: list[Employee]

        self.assertEqual(0, len(Employee.all()))
        self.assertEqual(0, len(Department.all()))
        test_employee = Employee(
            employee_id='NewEmployeeId',
            name='Deux Glaces',
            dob=datetime.date(1999, 12, 31),
        )

        test_department = Department(
            department_code='Weirdoes',
            name='Pythonistas!',
            employees=[test_employee],
        )

        self.assertEqual('NewEmployeeId', test_employee.employee_id)
        self.assertEqual('Deux Glaces', test_employee.name)
        self.assertEqual(datetime.date(1999, 12, 31), test_employee.dob)

        self.assertEqual('Weirdoes', test_department.department_code)
        self.assertEqual('Pythonistas!', test_department.name)
        self.assertEqual([test_employee], test_department.employees)
        self.assertIs(test_employee, test_department.employees[0])

        self.assertEqual(1, len(Employee.all()))
        retrieved_employee = Employee.find_one()
        self.assertIs(test_employee, retrieved_employee)
        self.assertEqual(datetime.date(1999, 12, 31), retrieved_employee.dob)

        del test_employee
        del test_department
        retrieved_employee = Employee.find_one()
        retrieved_dept = Department.find_one()
        self.assertEqual(datetime.date(1999, 12, 31), retrieved_employee.dob)
        self.assertIs(retrieved_dept.employees[0], retrieved_employee)
