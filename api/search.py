from sqlalchemy import and_, desc, or_

from reptile.SQL import SQL, products, platforms, times, evalresult
from reptile.dingshi import time_offset

import xmnlp as xm
import wordninja
import re

num_per_page = 25

def search(keyword, page):
    db = SQL('datadb')

    page = int(page)

    # 根据页码返回指定记录
    offset = int((page-1) * num_per_page)

    # 时间
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60

    # 关键词拆分
    keywords = []

    ch = re.findall('[\u4e00-\u9fa5]+', keyword)
    tp = ''
    for c in ch:
      tp = tp+c
    cnk = xm.seg(tp)

    enk = wordninja.split(keyword)

    keywords = enk[0:3] + cnk[0:3]
    words = keywords
    for i in range(0, len(keywords)):
        keywords[i] = '%' + str(keywords[i]) + '%'

    print(words)

    rule = or_(*[products.name.like(w) for w in keywords])

    rs = db.session.query(evalresult, products).join(products, evalresult.productid == products.id).filter(rule).filter(evalresult.current_timeid == timeid, evalresult.comm_eval>-1).offset(offset).all()


    datalist = []
    for result in rs:
        print(result[1].name)
        # 模糊匹配 筛选命中2个以上的
        print(len(words))

        if len(words)>=3:
            i=0
            for key in words:
                check = re.search(key, result[1].name)
                if check:
                    i+=1
                    print('+++')
            if i<3:
                continue
        result = result[0]
        data = {}
        tmp = result.imgid.split('||')
        data['imgid'] = 'https://www.buptdachuang2019.top/api/img?imgid='+tmp[0]
        data['productid'] = result.productid
        data['platform'] = db.session.query(platforms).filter(platforms.id == result.platformid).one().platform
        data['name'] = db.session.query(products).filter(products.id == result.productid).one().name
        data['price'] = result.price
        data['num'] = result.num
        datalist.append(data)
    db.close()

    return datalist

def searchAll(page):
    db = SQL('datadb')

    page = int(page)

    # 根据页码返回指定记录
    offset = int((page - 1) * num_per_page)

    # 时间
    timeid = db.session.query(times).order_by(desc(times.id)).first().id

    # timeid = 60
    rs = db.session.query(evalresult).filter(evalresult.current_timeid == timeid, evalresult.exp_pop>-1).limit(num_per_page).offset(offset).all()

    datalist = []
    for result in rs:
        if not result.exp_pop:
            continue
        data = {}
        tmp = result.imgid.split('||')
        data['imgid'] =  'https://www.buptdachuang2019.top/api/img?imgid='+tmp[0]
        data['productid'] = result.productid
        data['platform'] = db.session.query(platforms).filter(platforms.id == result.platformid).one().platform
        data['name'] = db.session.query(products).filter(products.id == result.productid).one().name
        data['price'] = result.price
        data['num'] = result.num
        datalist.append(data)

    db.close()

    return datalist

def searchbyid(id):
    db = SQL('datadb')

    # 时间
    timeid = db.session.query(times).order_by(desc(times.id)).first().id

    data = {}
    if id == "-1":
        data['productid'] = -1
        data['name'] = '暂无手机'
        data['imgid'] = 'https://www.buptdachuang2019.top/api/img?imgid='+ str(5333)
        db.close()
        return [data]

    # timeid = 60
    result = db.session.query(evalresult).filter(evalresult.current_timeid == timeid,evalresult.productid == id, evalresult.exp_pop>-1).first()


    if not result.exp_pop:
        return [data]
    tmp = result.imgid.split('||')
    data['imgid'] =  'https://www.buptdachuang2019.top/api/img?imgid='+tmp[0]
    data['productid'] = result.productid
    data['platform'] = db.session.query(platforms).filter(platforms.id == result.platformid).one().platform
    data['name'] = db.session.query(products).filter(products.id == result.productid).one().name
    data['price'] = result.price
    data['num'] = result.num

    db.close()

    return [data]

if __name__ == '__main__':
    search(id)