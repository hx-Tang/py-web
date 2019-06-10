from sqlalchemy import desc, and_

from reptile.SQL import SQL, platforms, evalresult, times, products

from reptile.dingshi import time_offset

num_per_page = 50


def hot(page, t):
    db = SQL('datadb')


    # 最近日期
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60

    page = int(page)

    # 根据页码返回指定记录
    offset = int((page-1) * num_per_page)

    rs = db.session.query(evalresult).filter(evalresult.current_timeid == timeid, evalresult.comm_eval>-1).order_by(desc(evalresult.score)).limit(num_per_page).offset(offset).all()

    datalist = []
    for result in rs:
        data = {}
        tmp = result.imgid.split('||')
        data['imgid'] =  'https://www.buptdachuang2019.top/api/img?imgid='+tmp[0]
        data['productid'] = result.productid
        data['platform'] = db.session.query(platforms).filter(platforms.id == result.platformid).one().platform
        name = db.session.query(products).filter(products.id == result.productid).one().name
        if len(name) >= 25:
            continue
        if t == '1':
            data['name'] = name
        else:
            data['name'] = name[0:12]
        data['price'] = result.price
        data['num'] = result.num
        data['score'] = result.score
        datalist.append(data)

    db.close()

    return datalist