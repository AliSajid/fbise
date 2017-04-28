from pony import orm

cleandb = orm.Database()


class Student(cleandb.Entity):
    rollno = orm.Required(int)
    name = orm.Required(str)
    father = orm.Required(str)
    result = orm.Required(str)
    institute = orm.Required(str)
    remarks = orm.Optional(str)
    subjects = orm.Set('Result')


class Result(cleandb.Entity):
    student = orm.Required(Student)
    subject = orm.Required(str)
    part = orm.Optional(str)
    theory = orm.Required(int)
    practical = orm.Optional(int, nullable=True)
