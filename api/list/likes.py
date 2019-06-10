from sqlalchemy import *

from reptile.SQL import SQL, products, platforms, evalresult, times
from reptile.dingshi import time_offset

num_per_page = 50

def likes(page):
    db = SQL('datadb')

    page = int(page)

    # 根据页码返回指定记录
    offset = int((page-1) * num_per_page)

    # 最新日期
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60
    rs = db.session.query(evalresult).filter(evalresult.current_timeid == timeid, evalresult.comm_eval>-1).order_by(desc(evalresult.exp_pop)).offset(offset).all()

    datalist = []
    for result in rs:
        data = {}
        tmp = result.imgid.split('||')
        data['imgid'] = 'https://www.buptdachuang2019.top/api/img?imgid='+tmp[0]
        data['productid'] = result.productid
        data['platform'] = db.session.query(platforms).filter(platforms.id == result.platformid).one().platform
        name = db.session.query(products).filter(products.id == result.productid).one().name
        if len(name) >= 25:
            continue
        data['name'] = name
        data['price'] = result.price
        data['num'] = result.num
        data['eval_pop'] = result.exp_pop
        datalist.append(data)
    db.close()

    return datalist