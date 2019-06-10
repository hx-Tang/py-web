from reptile.SQL import SQL, products, platforms, phones, phone_info,raw_info,evalresult, times, imgs
from sqlalchemy import *

def content(productid):

    db = SQL('datadb')

    # timeid = 60
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    rs = db.session.query(evalresult).filter(evalresult.productid == productid).filter(evalresult.current_timeid<=timeid).order_by(
        desc(evalresult.id)).first()

    data = {}
    # 商品图片id
    imgids = []
    try:
        tmp = rs.imgid.split('||')
        tmp.pop()
        for t in tmp:
            imgids.append('https://www.buptdachuang2019.top/api/img?imgid=' + t)
    except:
        pass
    data['imgids'] = imgids
    # 平台名
    data['platform'] = db.session.query(platforms).filter(platforms.id == rs.platformid).one().platform
    product = db.session.query(products).filter(products.id==productid).first().product
    # 商品链接
    if data['platform']=="JD":
        data['link'] = 'https://item.jd.com/' + str(product) +'.html'
    elif data['platform']=="SN":
        data['link'] = 'https://product.suning.com/' + str(product) +'.html'

    # 商品名
    data['name'] = db.session.query(products).filter(products.id == rs.productid).one().name

    # 当前销量
    data['num'] = rs.num
    # 销量预测
    tmp = []
    imgid = ''
    try:
        tmp = rs.num_trend.split('||')
        imgid = tmp.pop()
    except:
        pass
    data['num_trend'] = tmp
    data['num_imgid'] = 'https://www.buptdachuang2019.top/api/comm_img?imgid='+imgid
    # 历史销量列表
    numdic ={}
    nums = db.session.query(phones, times).join(times, times.id == phones.timeid).filter(
        phones.productid == productid).order_by(desc(phones.timeid)).all()
    for n in nums:
        numdic.update({n[1].time: n[0].num})
    data['numlist'] = numdic

    # 当前价格
    data['price'] = rs.price
    # 价格预测
    tmp = []
    imgid = ''
    try:
        tmp = rs.price_trend.split('||')
        imgid = tmp.pop()
    except:
        pass
    data['price_trend_raw'] = rs.price_trend
    data['price_trend'] = tmp
    data['price_imgid'] = 'https://www.buptdachuang2019.top/api/comm_img?imgid='+imgid
    # 历史价格列表
    pricedic ={}
    prices = db.session.query(phones, times).join(times, times.id == phones.timeid).filter(
        phones.productid == productid).order_by(desc(phones.timeid)).all()
    for pr in prices:
        pricedic.update({pr[1].time: pr[0].price})
    data['pricelist'] = pricedic

    # 商品原始参数信息
    r = db.session.query(raw_info).filter(raw_info.id == rs.infoid).one()
    dic ={}
    list = r.info.split("||")
    for index in range(1, int(len(list) / 2)):
        dic.update({list[2*index-1]: list[2*index]})
    data['info'] = dic

    # 产品打分
    data['score'] = rs.score
    # 产品打分细节
    r = rs.score_detail
    dic2 = {}
    try:
        list2 = r.split("||")
        for index in range(0, int(len(list2) / 2)):
            dic2.update({list2[2 * index]: list2[2 * index + 1]})
    except:
        pass
    data['score_detail_raw'] = r
    data['socre_detail'] = dic2

    pr = db.session.query(phone_info).filter(phone_info.productid == productid).first()
    dic3 = {}
    dic3['fpixel'] = pr.fpixel
    dic3['bpixel'] = pr.bpixel
    dic3['screen'] = pr.screen
    dic3['cpu'] = pr.cpu
    dic3['sim'] = pr.sim
    dic3['brand'] = pr.brand
    dic3['weight'] = pr.weight
    dic3['thick'] = pr.thick
    # 配置参数
    data['para'] = dic3
    # 产品兴趣度预测
    data['exp_pop'] = rs.exp_pop

    # 商品关键词
    data['keyword'] = rs.keywords
    # 近期好评度
    data['comm_eval'] = rs.comm_eval
    # 好评评论
    tmp = []
    try:
        tmp = rs.goodcomm.split("||")
        tmp.pop()
    except:
        pass
    data['goodcomm_raw'] = rs.goodcomm
    data['goodcomm'] = tmp
    # 差评评论
    tmp = []
    try:
        tmp = rs.badcomm.split("||")
        tmp.pop()
    except:
        pass
    data['badcomm_raw'] = rs.badcomm
    data['badcomm'] = tmp
    # 评论词云图id
    data['comm_imgid'] = 'https://www.buptdachuang2019.top/api/comm_img?imgid='+str(rs.comm_imgid)
    # 价格销量曲线
    data['price_num'] = 'https://www.buptdachuang2019.top/api/comm_img?imgid='+str(rs.price_num)


    db.close()

    return [data]
