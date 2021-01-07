from pony import orm
from pony.orm import Required, Optional, PrimaryKey, db_session, raw_sql

db = orm.Database()
db.bind(provider='sqlite', filename='db.sqlite', create_db=True)


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


with db_session():
    conn = db.get_connection()
    conn.create_function('REGEXP', 2, regexp)


class Item(db.Entity):
    source = Required(str)
    popular = Optional(str)
    title = Required(str)
    href = Required(str)
    summary = Required(str)
    read = Required(bool, default=False)


db.generate_mapping(create_tables=True)
