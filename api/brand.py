from sqlalchemy import desc

from reptile.config import brandlist

import numpy as np
from reptile.SQL import SQL, platforms, evalresult, times, products, nnresult

def brandscore(p):
    db = SQL('datadb')

    timeid = db.session.query(times).order_by(desc(times.id)).first().id

    oft = int(p)-1

    rs = db.session.query(nnresult).filter(nnresult.timeid <= timeid).order_by(desc(nnresult.id)).offset(oft).first()

    weightdic = rs.weightdic

    data = {}
    tmp = []
    try:
        tmp = weightdic.split('||')
        tmp.pop()
    except:
        pass
    # 读取品牌部分
    tmp = tmp[0:len(brandlist)]
    max = 0.0
    min = 0.0
    for t in tmp:
        c = float(t.split(':')[1])
        if c>max:
            max = c
        if c<min:
            min = c
    # print(max, '  ', min)
    # 归一化
    for t in tmp :
        data[t.split(':')[0]] = np.round((float(t.split(':')[1])-min)/(max-min)*10, 2)
        # data[t.split(':')[0]] = float(t.split(':')[1])
    db.close()
    return [data]

def getweight(weightdic):
    weight = []
    for w in weightdic:
        weight.append()

if __name__ == '__main__':
    print(brandscore())

