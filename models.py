from pony import orm

db = orm.Database()


class Record(db.Entity):
    idx = orm.Required(int)
    rollno = orm.Required(str)
    html = orm.Required(str)
    error = orm.Required(bool)


class Student(db.Entity):
    rollno = orm.Required(int)
    name = orm.Required(str)
    father = orm.Required(str)
    result = orm.Required(str)
    institute = orm.Required(str)


class Result(db.Entity):
    student = orm.Required(Student)
    subject = orm.Required(str)
    part = orm.Required(str)
    theory = orm.Required(int)
    practical = orm.Required(int)
