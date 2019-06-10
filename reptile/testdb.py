import sqlalchemy
from sqlalchemy import *

import SQL as DB
from SQL import *

# db = DB.SQL('datadb')
# tid = db.session.query(times).order_by(desc(times.id)).first().id
# li = db.session.query(phones).filter(phones.timeid==tid).all()
# timeid = 60
# page =1
# num_per_page=25
# offset = int((page - 1) * num_per_page)
#
# rs = db.session.query(evalresult).filter(evalresult.current_timeid == timeid).limit(num_per_page).offset(offset).all()
# print(rs)
# db.close()
# li = db.session.query(evalresult).filter(evalresult.current_timeid==60).all()
# for l in li:
#     print()
#     # print(db.get_comment(l.id))
for i in range(0, 10):
    print(i)