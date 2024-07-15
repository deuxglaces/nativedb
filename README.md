# NativeDB

NativeDB is an ORM model for MongoDB.

Write MongoDB models like you would write a dataclass:

    @database('MyDatabase')
    class Company(MongoDbModel):
        registration_number: int
        name: str
        incorporated: datetime.datetime

You can create complex models by including one model in another:

    @database('MyDatabase')
    class Employee(MongoDbModel):
        employee_id: int
        company: Company

To retrieve an object from the database:

    company = Company.find_one(name='Python Inc.')

To get all objects matching a particular query:

    employees = Employee.find(company=company)

To make a change to the company:

    company.name = 'Pythonistas Inc.'
    company.save()  # writes to database

Or update and write fields in one line:

    company.update(name='Snakes Inc.')
