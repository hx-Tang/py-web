import sqlalchemy
from sqlalchemy import *

import SQL as DB
from SQL import evalresult, products, times, models, phones, stores, phone_info, raw_info, imgs

import re

from config import cpulist1, cpulist2, cpulist3, cpulist4, brandlist

'''
预生成结果表、商品型号对齐、配置信息拆分
型号对齐: 用结果表销量最高的名字，搜，一个店出一个商品号，每种手机用销量前三的数据
'''


# 预生成结果表
def preproc(dbname):
    db = DB.SQL(dbname)
    # 当前时间
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 65
    # 全部产品
    productlist = db.session.query(products).order_by(desc(products.id)).all()
    # productlist = db.session.query(products).filter(products.platformid == 4).all()
    # 搜索产品最近一条爬虫记录
    for p in productlist:
        id = p.id
        record = db.session.query(phones).filter(phones.productid == id).filter(phones.timeid<=timeid).order_by(desc(phones.id)).first()
        print('--------')
        name = p.name
        print(name)
        if not record:
            print(str(id) + '号商品无记录')
            continue
        if record.timeid<timeid-5:
            print(str(id) + '号商品记录过期')
            continue



        # # 已有结果表数据则跳过 针对多次重复运行的处理
        # if db.session.query(evalresult).filter(evalresult.current_timeid == timeid,
        #                                        evalresult.productid == record.productid).first():
        #     print(str(id) + '号商品已处理')
        #     continue

        print(id, '号商品-爬虫记录：', record.id)

        # 商品参数出错跳过
        if not db.session.query(phone_info).filter(phone_info.productid == record.productid).first():
            print('商品参数出错记录无效')
            continue

        res = db.session.query(evalresult, products, stores).join(products, products.id == evalresult.productid).join(
            stores, stores.id == evalresult.storeid).filter(
            products.name == name, evalresult.storeid == record.storeid, evalresult.current_timeid == timeid).first()
        # 若已有同店同名数据
        if res:
            print(res[0].data_timeid)
            # 数据更新则替换
            if res[0].data_timeid <= record.timeid:
                obj = db.session.query(evalresult).filter(evalresult.id == res[0].id).first()
                print('替换同店同名旧结果：' + str(obj.id))
                obj.current_timeid = timeid
                obj.data_timeid = record.timeid
                obj.productid = record.productid
                obj.platformid = record.platformid
                obj.storeid = record.storeid
                try:
                    obj.infoid = db.session.query(raw_info).filter(raw_info.pid == record.id).first().id
                except:
                    print('no info')
                obj.price = record.price
                obj.goodrate = record.goodrate
                obj.num = record.num
                img = db.session.query(imgs).filter(imgs.pid == record.id).all()
                imgids = ''
                for i in img:
                    imgids = imgids + str(i.id) + '||'
                obj.imgid = imgids
                try:
                    db.session.commit()
                    print('success')
                except:
                    print('ex')
                    db.session.rollback()
            # 更旧则跳过
            continue
        img = db.session.query(imgs).filter(imgs.pid == record.id).all()
        imgids = ''
        for i in img:
            imgids = imgids + str(i.id) + '||'
        try:
            infoid = db.session.query(raw_info).filter(raw_info.pid == record.id).first().id
            obj = evalresult(current_timeid=timeid, data_timeid=record.timeid, productid=record.productid,
                             platformid=record.platformid, storeid=record.storeid, infoid=infoid, imgid=imgids, price=record.price,
                             goodrate=record.goodrate, num=record.num)
        except:
            obj = evalresult(current_timeid=timeid, data_timeid=record.timeid, productid=record.productid,
                             platformid=record.platformid, storeid=record.storeid, imgid=imgids, price=record.price,
                             goodrate=record.goodrate, num=record.num)
        # 添加一条结果表记录
        try:
            db.session.add(obj)
            db.session.commit()
            print('success')
        except sqlalchemy.exc.IntegrityError as ex:
            print(ex)
            db.session.rollback()
    db.close()


# 商品型号对齐
# def Modelalignment(dbname):
#     db = DB.SQL(dbname)
#
#     # 当前时间
#     timeid = db.session.query(times).order_by(desc(times.id)).first().id
#     print(timeid)
#
#     # 已有型号赋值：
#     # 型号列表
#     modellist = db.session.query(models).all()
#     # 拿出一个型号
#     # if 0:
#     if modellist:
#         for m in modellist:
#             modelid = m.id  # 获取id
#             model = m.model  # 获取型号名
#             model = [model]
#
#             # 获取代表商品
#             result = db.session.query(evalresult).filter(
#                 and_(evalresult.current_timeid == timeid, products.modelid == modelid)).first()
#             if result is None:
#                 continue
#
#             # 计算价格区间
#             r = int(result.num / 10)
#
#             # 用型号名去搜手机 销量降序
#             words = []
#             for key in model:
#                 words.append('%' + str(key) + '%')
#
#             # 搜索规则：名称类似, 符合价格区间，销量大于10000, 店铺号不重复, 销量前三
#             rule = and_(*[products.name.like(w) for w in words], evalresult.current_timeid == timeid,
#                         (evalresult.price - r) < evalresult.price, evalresult.price < (evalresult.price + r),
#                         evalresult.num > 10000)
#             # 获取结果
#             rs = db.session.query(evalresult, products).join(products, products.id == evalresult.productid).filter(
#                 rule).order_by(
#                 desc(evalresult.num)).distinct(evalresult.storeid).limit(3).all()
#             # 填入型号
#             for p in rs:
#                 # 跳过型号已经定义的
#                 if p[1].modelid is not None:
#                     continue
#                 print(str(p[0].num) + ' ' + str(p[0].data_timeid) + ' ' + p[1].name + ' ' + str(p[1].id))
#                 productid = p[0].productid
#                 product = db.session.query(products).filter(products.id == productid).first()
#                 product.modelid = modelid
#                 try:
#                     db.session.commit()
#                 except sqlalchemy.exc.IntegrityError as ex:
#                     print(ex)
#                     db.session.rollback()
#
#     # 查询是否有新型号出现：
#     # 提取销量前50
#     list = db.session.query(evalresult, products, stores).join(products, products.id == evalresult.productid).join(
#         stores, stores.id == evalresult.storeid).filter(
#         evalresult.current_timeid == timeid, evalresult.num > 10000).order_by(desc(evalresult.num)).limit(
#         50).all()
#     # 打印目前的前50
#     for lr in list:
#         print(str(lr[0].num) + ' ' + str(lr[0].data_timeid) + ' ' + lr[1].name + ' ' + str(lr[1].modelid) + ' ' + lr[
#             2].name)
#     if 1:  # 调试开关
#         # 拿出其中一个
#         for result in list:
#             # 型号未定义的
#             if result[1].modelid is not None:
#                 continue
#
#             # TODO 拆分他的名字去掉品牌名
#             name = result[1].name
#             '''
#             nlp拆词
#             '''
#             name = [name]
#             print(name)
#
#             if db.session.query(models).filter(models.model == name[0]).first():
#                 print('型号存在跳过')
#                 continue
#             # 存入model表
#             obj = models(model=name[0])
#             try:
#                 db.session.add(obj)
#                 db.session.commit()
#             except sqlalchemy.exc.IntegrityError as ex:
#                 print(ex)
#                 db.session.rollback()
#                 continue  # 失败跳过这个手机
#             except sqlalchemy.exc.DataError as ex:
#                 print(ex)
#                 db.session.rollback()
#                 continue  # 失败跳过这个手机
#             modelid = db.session.query(models).filter(models.model == name[0]).first().id
#
#             # 用这个名字去搜手机 销量降序
#             words = []
#             for key in name:
#                 words.append('%' + str(key) + '%')
#             # 价格区间
#             r = int(result[0].num / 10)
#             # 搜索规则：名称类似, 符合价格区间，销量大于10000, 店铺号不重复, 销量前三
#             rule = and_(*[products.name.like(w) for w in words], evalresult.current_timeid == timeid,
#                         (evalresult.price - r) < evalresult.price, evalresult.price < (evalresult.price + r),
#                         evalresult.num > 10000)
#             # 获取结果
#             rs = db.session.query(evalresult, products).join(products, products.id == evalresult.productid).filter(
#                 rule).order_by(
#                 desc(evalresult.num)).distinct(evalresult.storeid).limit(3).all()
#             # 填入型号
#             for p in rs:
#                 # 跳过型号已经定义的
#                 if p[1].modelid is not None:
#                     continue
#                 print(str(p[0].num) + ' ' + str(p[0].data_timeid) + ' ' + p[1].name + ' ' + str(p[1].id))
#                 productid = p[0].productid
#                 product = db.session.query(products).filter(products.id == productid).first()
#                 product.modelid = modelid
#                 try:
#                     db.session.commit()
#                 except sqlalchemy.exc.IntegrityError as ex:
#                     print(ex)
#                     db.session.rollback()
#     db.close()


# 配置信息拆分
'''
商品参数数字化
'''


def fragment(dbname):
    db = DB.SQL(dbname)
    # 时间戳
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 65
    # # 取当天的所有手机
    phonelist = db.session.query(phones, raw_info).join(raw_info, raw_info.pid == phones.id).filter(
        phones.timeid == timeid).all()
    # # 取当天的所有手机
    # phonelist = db.session.query(phones, raw_info).join(raw_info, raw_info.pid == phones.id).filter(
    #     phones.timeid == timeid, phones.platformid == 4).all()

    for p in phonelist:
        # rawinfo 每个手机未拆分的参数 @String

        rawinfo = p[1].info
        print('------------------')
        print(p[0].id)
        print(db.session.query(products).filter(products.id == p[0].productid).first().product)
        print(rawinfo)

        flg = 0
        # 拆分后数据所在对象
        res = db.session.query(phone_info).filter(phone_info.productid==p[0].productid).first()
        if not res:
            res = phone_info(productid=p[0].productid)
            flg = 1

        # TODO 拆分操作 拆完的存到res里
        info = rawinfo.split("||")
        print(info)
        res.brand = '其他'
        res.weight = "Weight N/A"
        res.thick = "Thick N/A"
        res.screen = "Screen N/A"
        res.fpixel = "Fpixel N/A"
        res.bpixel = "Bpixel N/A"
        res.cpu = 1
        res.sim = "1"
        res.year = "N/A"
        res.month = "N/A"
        for index in range(1, int(len(info) / 2)):
            if "机身重量" in info[2 * index - 1] or "重量" in info[2 * index - 1]:
                if "约" in info[2 * index]:
                    info[2 * index] = (info[2 * index].split("约"))[1]
                if "克" in info[2 * index]:
                    weight = info[2 * index].split("克")
                    res.weight = weight[0]
                if "g" in info[2 * index]:
                    weight = info[2 * index].split("g")
                    res.weight = weight[0]
                check = (info[2 * index]).split(".")
                if info[2 * index].isdigit() or check[0].isdigit():
                    res.weight = info[2 * index]
            if "机身厚度" in info[2 * index - 1] or "厚度" in info[2 * index - 1]:
                thick = re.findall(r"\d+\.?\d*", info[2 * index])
                if len(thick) > 0:
                    res.thick = thick[0]
            #    if "约" in info[2 * index]:
            #        info[2 * index] = (info[2 * index].split("约"))[1]
            #    if "毫" in info[2 * index]:
            #        thick = info[2 * index].split("毫")
            #        res.thick = thick[0]
            #    if "mm" in info[2 * index]:
            #        thick = info[2 * index].split("mm")
            #        res.thick = thick[0]
            #    check = (info[2 * index]).split(".")
            #    if info[2 * index].isdigit() or check[0].isdigit():
            #        res.thick = info[2 * index]
            if info[2 * index - 1] == "前置摄像头" or info[2 * index - 1] == "前摄像头":
                fcamera = info[2 * index].split("万")
                camera = fcamera[0]
                digcamera=''
                if "x" in camera:
                    digcamera = camera.split("x")[1]
                if "双" in camera:
                    digcamera = camera.split("双")[1]
                if "+" in camera:
                    digcamera = camera.split("+")[0]
                if camera.isdigit():
                    digcamera = camera
                if digcamera.isdigit():
                    res.fpixel = digcamera
            if info[2 * index - 1] == "后置摄像头" or info[2 * index - 1] == "后摄像头":
                bcamera = info[2 * index].split("万")
                camera = bcamera[0]
                if "x" in camera:
                    digcamera = camera.split("x")[1]
                if "双" in camera:
                    digcamera = camera.split("双")[1]
                if "+" in camera:
                    digcamera = camera.split("+")[0]
                if camera.isdigit():
                    digcamera = camera
                if digcamera.isdigit():
                    res.bpixel = digcamera
            if info[2 * index - 1] == "主屏幕尺寸（英寸）" or info[2 * index - 1] == "主屏幕尺寸" or info[2 * index - 1] == "屏幕尺寸":
                screensize = info[2 * index].split("英")
                res.screen = screensize[0]
            if "CPU" in info[2 * index - 1]:
                for cpukey in cpulist1:
                    check = re.search(cpukey, info[2 * index])
                    if check:
                        res.cpu = 5
                        break
                for cpukey in cpulist2:
                    check = re.search(cpukey, info[2 * index])
                    if check:
                        res.cpu = 4
                        break
                for cpukey in cpulist3:
                    check = re.search(cpukey, info[2 * index])
                    if check:
                        res.cpu = 3
                        break
                for cpukey in cpulist4:
                    check = re.search(cpukey, info[2 * index])
                    if check:
                        res.cpu = 2
                        break
            if info[2 * index - 1] == "最大支持SIM卡数量":
                simnum = info[2 * index].split("个")
                res.sim = simnum[0]
            if p[0].platformid == 4:
                if "上市时间" in info[2 * index - 1]:
                    date = re.findall(r"\d+?\d*", info[2 * index])
                    if len(date) > 1:
                        res.year = re.findall(r"\d+?\d*", info[2 * index])[0]
                        res.month = re.findall(r"\d+?\d*", info[2 * index])[1]
            else:
                if "上市年份" in info[2 * index - 1]:
                    year = re.findall(r"\d+\.?\d*", info[2 * index])
                    if year:
                        res.year = year[0]
                if "上市月份" in info[2 * index - 1]:
                    month = re.findall(r"\d+\.?\d*", info[2 * index])
                    if month:
                        res.month = month[0]
            if info[2 * index - 1] == "品牌":
                for brandkey in brandlist:
                    check = re.search(brandkey, info[2 * index])
                    if check:
                        res.brand = brandkey
                print("品牌: " + res.brand)
                if res.brand == "Apple" or res.brand == "APPLE" or res.brand == "苹果":
                    res.cpu = 5

        print("重量: " + res.weight)
        print("厚度: " + res.thick)
        print("前置摄像头: " + res.fpixel)
        print("后置摄像头: " + res.bpixel)
        print("屏幕尺寸: " + res.screen)
        print("CPU: " + str(res.cpu))
        print("最大支持SIM卡数量: " + str(res.sim))
        print("上市年份: " + str(res.year))
        print("上市月份: " + str(res.month))

        chweight = res.weight
        ccweight = chweight.split(".")
        chthick = res.thick
        ccthick = chthick.split(".")
        chscreen = res.screen
        ccscreen = chscreen.split(".")
        chfpixel = res.fpixel
        chbpixel = res.bpixel
        chsim = res.sim
        chyear = res.year
        chmonth = res.month
        if (ccweight[0]).isdigit() or chweight.isdigit():
            if (ccthick[0]).isdigit() or chthick.isdigit():
                if (ccscreen[0]).isdigit() or chscreen.isdigit():
                    if chfpixel.isdigit():
                        if chbpixel.isdigit():
                            if chsim.isdigit():
                                if chyear.isdigit() and chyear != 0:
                                    if chmonth.isdigit() and chmonth != 0:
                                        print("Success")
                                        try:
                                            if flg==1:
                                                db.session.add(res)
                                            db.session.commit()
                                            continue
                                        except sqlalchemy.exc.DataError as ex:
                                            db.session.rollback()
        db.session.rollback()

if __name__ == '__main__':
    fragment('datadb')
    # preproc('datadb')
    # Modelalignment('testdb')
