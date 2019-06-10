from sqlalchemy import desc

from reptile.config import brandlist
import re
from reptile.SQL import SQL, platforms, evalresult, times, products, nnresult
from reptile.neuranetwork import NeuralNetwork
from numpy import array
import numpy as np

p1 = (0,1500)
p2 = (1500,2500)
p3 = (2500,4000)
p4 = (4000,6000)
p5 = (6000,10000)


def NNt(p,weight):
    db = SQL('datadb')

    timeid = db.session.query(times).order_by(desc(times.id)).first().id-1

    nn = db.session.query(nnresult).filter(nnresult.timeid == timeid).order_by(desc(nnresult.id)).first()

    fpixelmax = nn.fpixelmax
    bpixelmax = nn.bpixelmax
    screenmax = nn.screenmax
    thickmax = nn.thickmax
    weightmax = nn.weightmax
    print(fpixelmax,bpixelmax,screenmax,thickmax,weightmax)

    # 预处理
    t = []
    # 品牌列表
    brand = p["brand"]
    if brand == None:
        brand = ''
    blist = []
    flg = 0
    for key in brandlist:
        check = re.search(key, brand)
        if check:
            blist.append(1)
            flg = 1
        else:
            blist.append(0)
    if flg == 0:
        blist.append(1)
    else:
        blist.append(0)
    t += blist

    t.append(p["fpixel"] / fpixelmax)
    t.append(1 - p["bpixel"] / bpixelmax)
    t.append(p["cpu"] / 5)
    t.append(1 - p["screen"] / screenmax)
    t.append(p["sim"] / 2)
    t.append(p["thick"] / thickmax)
    t.append(p["weight"] / weightmax)

    # TODO 加载nn
    neural_network = NeuralNetwork()
    neural_network.synaptic_weights = weight

    # TODO 预测
    ans = neural_network.think(array(t))
    print(p['price'])
    minp,maxp = getprice(int(p['price']))
    print(minp, maxp)

    # TODO 预测结果存入这个ans里
    ans = np.round(ans[0], 2)
    ans = int(ans*100*(1-minp/10000))

    print(ans)
    # 返回三个数
    data = {}
    try:
        data['lower'] = db.session.query(evalresult).filter(evalresult.current_timeid == timeid,evalresult.exp_pop >= 0,evalresult.exp_pop < ans).filter(evalresult.price < maxp, evalresult.price > minp).order_by(
            desc(evalresult.exp_pop)).first().productid

    except:
        data['lower'] = -1
    print(data['lower'])
    try:
        data['higher'] = db.session.query(evalresult).filter(evalresult.current_timeid == timeid,evalresult.exp_pop >= ans).filter(evalresult.price < maxp, evalresult.price > minp).order_by(
            evalresult.exp_pop).first().productid
    except:
        data['higher'] = -1
    print(data['higher'])
    data['ans'] = ans
    ls = db.session.query(evalresult).filter(evalresult.current_timeid == timeid, evalresult.exp_pop >= 0).filter(evalresult.price < maxp, evalresult.price > minp).order_by(
        desc(evalresult.exp_pop)).all()
    lo = db.session.query(evalresult).filter(evalresult.current_timeid == timeid, evalresult.exp_pop >= 0, evalresult.exp_pop < ans).filter(evalresult.price < maxp, evalresult.price>minp).order_by(
        desc(evalresult.exp_pop)).all()
    hi = db.session.query(evalresult).filter(evalresult.current_timeid == timeid,evalresult.exp_pop >= ans).filter(evalresult.price < maxp, evalresult.price > minp).order_by(
            evalresult.exp_pop).all()
    print(len(lo)/len(ls))
    print(len(hi)/len(ls))

    data['rate'] = int(len(lo)/len(ls)*100)

    db.close()
    return data


def NNn(p):
    db = SQL('datadb')
    timeid = 60

    ans = 10

    data = {}
    data['higher'] = db.session.query(evalresult).filter(evalresult.current_timeid == timeid,
                                                         evalresult.exp_pop < ans).order_by(
        desc(evalresult.exp_pop)).first().productid
    data['lower'] = db.session.query(evalresult).filter(evalresult.current_timeid == timeid,
                                                        evalresult.exp_pop > ans).order_by(
        evalresult.exp_pop).first().productid
    data['ans'] = ans

    db.close()
    return [data]


def getweight(weightdic):
    weight = []
    for w in weightdic:
        weight.append(float(w.split(':')[1]))
    return weight


def getprice(price):
    if price == 1:
        return p1[0], p1[1]
    if price == 2:
        return p2[0], p2[1]
    if price == 3:
        return p3[0], p3[1]
    if price == 4:
        return p4[0], p4[1]
    if price == 5:
        return p5[0], p5[1]
    return 0, 1500


def nn(p):
    db = SQL('datadb')
    a=[]
    wht=[]
    timeid = db.session.query(times).order_by(desc(times.id)).first().id-1

    offset = int(p['price']) - 1

    nn = db.session.query(nnresult).filter(nnresult.timeid == timeid).order_by(desc(nnresult.id)).offset(offset).first()

    weightdic = nn.weightdic.split('||')
    weightdic.pop()
    weight = getweight(weightdic)
    for w in weight:
        a.append(w)
        wht.append(a)
        a=[]

    result = NNt(p, array(wht))

    return [result]


if __name__ == '__main__':
    db = SQL('datadb')
    a=[]
    wht=[]
    timeid = db.session.query(times).order_by(desc(times.id)).first().id

    nn = db.session.query(nnresult).filter(nnresult.timeid == timeid).order_by(desc(nnresult.id)).first()
    weightdic = nn.weightdic.split('||')
    weightdic.pop()
    weight = getweight(weightdic)
    for w in weight:
        a.append(w)
        wht.append(a)
        a=[]

    phone = {}
    phone['brand'] = 'Apple'
    phone['fpixel'] = 700
    phone['bpixel'] = 1200
    phone['cpu'] = 5
    phone['screen'] = 6.1
    phone['sim'] = 2
    phone['thick'] = 8.3
    phone['weight'] = 194
    #print(phone)

    result = NNt(phone,array(wht))

    print(result)

    db.close()
