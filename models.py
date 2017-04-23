from pony import orm

db = orm.Database()


class Record(db.Entity):
    idx = orm.Required(int)
    rollno = orm.Required(str)
    html = orm.Required(str)
    error = orm.Required(bool)
