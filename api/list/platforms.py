from sqlalchemy import desc, and_

from reptile.SQL import SQL, products, evalresult, times, phones
from reptile.dingshi import time_offset
num_per_page = 50


# TODO 各平台商品综合表
def platforms(platformid, sort, page, t):
    db = SQL('datadb')

    page = int(page)

    # 根据页码返回指定记录
    offset = int((page - 1) * num_per_page)
    # 最近日期
    timeid = db.session.query(times).order_by(desc(times.id)).first().id

    # timeid = 60
    rule = and_(evalresult.platformid == platformid, evalresult.current_timeid == timeid, evalresult.exp_pop>-1, evalresult.comm_eval>-1)
    # 各种排序方式
    if sort == '1':
        rs = db.session.query(evalresult).filter(rule).order_by(evalresult.price).limit(num_per_page).offset(
            offset).all()
    elif sort == '2':
        rs = db.session.query(evalresult).filter(rule).order_by(desc(evalresult.price)).limit(
            num_per_page).offset(offset).all()
    elif sort == '3':
        rs = db.session.query(evalresult).filter(rule).order_by(evalresult.num).limit(num_per_page).offset(
            offset).all()
    elif sort == '4':
        rs = db.session.query(evalresult).filter(rule).order_by(desc(evalresult.num)).limit(num_per_page).offset(
            offset).all()
    else:
        rs = db.session.query(evalresult).filter(rule).order_by(desc(evalresult.productid)).limit(
            num_per_page).offset(offset).all()

    datalist = []
    for result in rs:
        data = {}
        tmp = result.imgid.split('||')
        data['imgid'] = 'https://www.buptdachuang2019.top/api/img?imgid='+tmp[0]
        data['productid'] = result.productid
        name = db.session.query(products).filter(products.id == result.productid).one().name
        if t == '1':
            data['name'] = name
        else:
            data['name'] = name[0:12]
        data['price'] = result.price
        data['num'] = result.num
        datalist.append(data)

    db.close()

    return datalist
