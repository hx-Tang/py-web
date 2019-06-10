import os
import csv

import sqlalchemy
from sqlalchemy import *

import pandas as pd
import matplotlib.pyplot as plt

from neuranetwork import NeuralNetwork
import SQL as DB
from SQL import phones, products, models, evalresult, times, stores, phone_info, raw_info, nnresult, comm_img

from numpy import array
import pandas as pd
import numpy as np
from fbprophet import Prophet

from config import brandlist

import NLP

import logging

import re

import operator

import time

import datetime

# TODO 对应的数据库表更新！ 完成
# TODO 后端热门列表和受欢迎列表接口编写
'''
每日自动数据分析：评论打分、关键字提取，价格预测，销量预测，（参数分析），整体打分
生成热门商品
'''


# 各种分析：参数拆解、nlp、预测...
def evalation(dbname):
    db = DB.SQL(dbname)

    # 时间戳
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60
    # 今日待分析
    list = db.session.query(evalresult, products, stores).join(products, products.id == evalresult.productid).join(
        stores, stores.id == evalresult.storeid).filter(evalresult.current_timeid == timeid).order_by(
        desc(evalresult.num)).all()
    list = db.session.query(evalresult, products, stores).join(products, products.id == evalresult.productid).join(
        stores, stores.id == evalresult.storeid).filter(evalresult.current_timeid == timeid).filter(evalresult.platformid == 4).order_by(
        desc(evalresult.num)).all()
    i = 0
    for l in list:
        i += 1
        print(str(i) + ' | ' + str(l[0].platformid) + ' ' + str(l[0].num) + ' ' + str(l[0].data_timeid) + ' ' + l[
            1].name + ' ' + str(
            l[0].price) + ' ' + str(l[0].num) + ' ' + l[2].name)
    i = 0
    for l in list:
        productid = l[0].productid
        i += 1
        print(str(i) + ' | ' + str(l[0].platformid) + ' ' + str(l[0].num) + ' ' + str(l[0].data_timeid) + ' ' + l[
            1].name + ' ' + str(
            l[0].price) + ' ' + str(l[0].num) + ' ' + l[2].name)

        logging.info(str(i) + ' | ' + str(l[0].num) + ' ' + str(l[0].data_timeid) + ' ' + l[1].name + ' ' + str(
            l[0].price) + ' ' + l[2].name + '\r')
        # TODO 价格预测
        # 历史价格：
        prices = db.session.query(phones, times).join(times, times.id == phones.timeid).filter(
            phones.productid == productid).order_by(phones.timeid).all()

        # 打印
        pricedic = {}
        for pr in prices:
            pricedic.update({pr[1].time: pr[0].price})
        print(pricedic)
        # 输出数据写入CSV文件
        with open('price.csv', 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(('ds', 'y'))
            for pr in prices:
                csv_writer.writerow((pr[1].time, pr[0].price))

        # 预测值放进来
        price_trend = []
        price_origin = []
        Pdate_origin = []
        Pdate = []

        df = pd.read_csv('price.csv')
        df.head()
        try:
            m = Prophet()
            m.fit(df)
            future = m.make_future_dataframe(periods=5)
            forecast = m.predict(future)
            a = forecast[['ds', 'yhat']]

            for i in range(0, df.shape[0]):  # 填加已有数据值
                price_origin.append(int(a.ix[i][1]))
                Pdate_origin.append(str(a.ix[i][0])[0:10])

            for i in range(df.shape[0], df.shape[0] + 5):
                price_trend.append(int(a.ix[i][1]))
                Pdate.append(str(a.ix[i][0])[0:10])

            fig = plt.figure(figsize=(18, 6.5))
            plt.plot(Pdate_origin, price_origin, marker='o', color='b', label='origin data')  # 画原始数据曲线
            for a, b in zip(Pdate_origin[0:-1:2], price_origin[0:-1:2]):  # 标注每点的值
                plt.text(a, b, b, ha='center', va='bottom', fontsize=20)

            plt.plot(Pdate, price_trend, marker='o', color='r', label='predicted data')  # 画预测数据曲线
            for a, b in zip(Pdate[0:-1:2], price_trend[0:-1:2]):  # 标注每点的值
                plt.text(a, b, b, ha='center', va='bottom', fontsize=20)
            fig.autofmt_xdate()
            plt.tight_layout()
            plt.xlabel('dateframe')
            plt.ylabel("price' value")
            plt.legend()

        except Exception as ex:
            print(ex)
        os.remove("price.csv")

        # 查看预测结果
        print('价格预测：  ', price_trend)

        plt.savefig('pi.png')

        try:
            fp = open("pi.png", 'rb')
            img = fp.read()
            fp.close()
            os.remove("pi.png")
            print('success')
        except Exception as e:
            print("价格图导入出错")
            logging.info("价格图导入出错\r")
            db.session.rollback()
            continue

        obj = comm_img(img=img)
        try:
            db.session.add(obj)
            db.session.commit()
            logging.info("价格图存储成功\r")
        except sqlalchemy.exc.DataError as ex:
            print("价格图存储出错")
            logging.info("价格图存储出错\r")
            db.session.rollback()
            continue

        imgid = db.session.query(comm_img).order_by(desc(comm_img.id)).first().id
        tmp = ''
        for n in price_trend:
            tmp = tmp + str(n) + '||'

        # 存回
        l[0].price_trend = tmp + str(imgid)
        logging.info('价格预测: ' + tmp + str(imgid) + '\r')
        try:
            db.session.commit()
            logging.info("价格预测存储成功\r")
        except sqlalchemy.exc.DataError as ex:
            db.session.rollback()

        # TODO 销量预测
        # 历史销量：
        nums = db.session.query(phones, times).join(times, times.id == phones.timeid).filter(
            phones.productid == productid).order_by(phones.timeid).all()

        # 输出数据写入CSV文件
        with open('num.csv', 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(('ds', 'y'))
            for nu in nums:
                csv_writer.writerow((nu[1].time, nu[0].num))

        # 预测值放进来
        num_trend = []
        num_origin = []
        date_trend = []
        date_origin = []

        df = pd.read_csv('num.csv')
        df.head()
        try:
            m = Prophet()
            m.fit(df)
            future = m.make_future_dataframe(periods=5)
            forecast = m.predict(future)
            a = forecast[['ds', 'yhat']]

            for i in range(0, df.shape[0]):  # 填加已有数据值
                num_origin.append(int(a.ix[i][1]))
                date_origin.append(str(a.ix[i][0])[0:10])

            for i in range(df.shape[0], df.shape[0] + 5):
                num_trend.append(int(a.ix[i][1]))
                date_trend.append(str(a.ix[i][0])[0:10])
            fig = plt.figure(figsize=(18, 6.5))
            plt.plot(date_origin, num_origin, marker='o', color='b', label='origin data')  # 画原始数据曲线
            tmp1 = date_origin[0:-1:2]
            tmp2 = num_origin[0:-1:2]
            for a, b in zip(tmp1, tmp2):  # 标注每点的值
                plt.text(a, b, b, fontsize=10)
            plt.plot(date_trend, num_trend, marker='o', color='r', label='predicted data')  # 画预测数据曲线
            tmp1 = date_trend[0:-1:2]
            tmp2 = num_trend[0:-1:2]
            for a, b in zip(tmp1, tmp2):  # 标注每点的值
                plt.text(a, b, b, fontsize=10)
            fig.autofmt_xdate()
            plt.xlabel('dateframe')
            plt.ylabel("sales' value")
            plt.legend()

        except Exception as ex:
            print(ex)
        os.remove("num.csv")

        # 查看预测结果
        print('销量预测：  ', num_trend)

        plt.savefig('ni.png')
        # 图片存入
        try:
            fp = open("ni.png", 'rb')
            img = fp.read()
            fp.close()
            os.remove("ni.png")
        except Exception as e:
            print("销量图导入出错")
            logging.info("销量图导入出错\r")
            db.session.rollback()
            continue

        obj = comm_img(img=img)
        try:
            db.session.add(obj)
            db.session.commit()
            logging.info("销量图存储成功\r")
        except sqlalchemy.exc.DataError as ex:
            print("销量图存储出错")
            logging.info("销量图存储出错\r")
            db.session.rollback()
            continue
        imgid = db.session.query(comm_img).order_by(desc(comm_img.id)).first().id
        # 数字存入
        tmp = ''
        for n in num_trend:
            tmp = tmp + str(n) + '||'
        l[0].num_trend = tmp + str(imgid)
        logging.info('销量预测: ' + tmp + str(imgid) + '\r')
        try:
            db.session.commit()
            logging.info("销量预测存储成功\r")
        except sqlalchemy.exc.DataError as ex:
            db.session.rollback()

        # TODO 评论分析
        # 本次所有评论：
        pid = db.session.query(phones).filter(phones.timeid == l[0].data_timeid,
                                              phones.productid == productid).first().id
        # logging.info(str(pid))
        commentlist = db.get_comment(pid)
        print(commentlist)
        while '' in commentlist:
            commentlist.remove('')
        if len(commentlist) == 0:
            print('无评论')
            logging.info("无评论\r")
            continue
        nlp = NLP.NLP()

        comm_eval = nlp.comment_Analysis(commentlist) % 100

        badcomm, goodcomm = nlp.comment_extract(commentlist)

        keywords = ''
        try:
            for txt in nlp.keyword_extract(commentlist):
                keywords = keywords + txt + '||'
        except:
            logging.info("keyword出错\r")
            pass
        try:
            nlp.word_cloud(commentlist)
        except Exception as ex:
            logging.info(ex)
            logging.info("词云图生成出错\r")
            pass
        try:
            fp = open("wc.png", 'rb')  # 注意这里一定要使用rb，读出二进制文件，否则有读不全等问题
            img = fp.read()
            fp.close()
            os.remove("wc.png")
            print('success')
        except Exception as e:
            print("词云导入出错")
            logging.info("词云导入出错\r")
            db.session.rollback()
            continue

        obj = comm_img(img=img)
        try:
            db.session.add(obj)
            db.session.commit()
            logging.info("词云存储成功\r")
        except sqlalchemy.exc.DataError as ex:
            print("词云存储出错")
            logging.info("词云存储出错\r")
            db.session.rollback()
            continue

        img = db.session.query(comm_img).order_by(desc(comm_img.id)).first().id
        l[0].comm_imgid = img
        l[0].comm_eval = comm_eval*100
        print(comm_eval)
        tmp = ""
        for g in goodcomm:
            tmp = tmp + g + "||"
        l[0].goodcomm = tmp
        print('goocom: ', tmp)
        tmp = ""
        for b in badcomm:
            tmp = tmp + b + "||"
        l[0].badcomm = tmp
        print('badcom:', tmp)
        l[0].keywords = keywords
        print('keywords:', keywords)
        try:
            db.session.commit()
            logging.info("nlp存储成功\r")
        except sqlalchemy.exc.DataError as ex:
            print(ex)
            print('nlp 存储出错')
            logging.info("nlp存储出错\r")
            db.session.rollback()


'''
各项参数分值赋值 打分
'''


def getscore(dbname, minp, maxp):
    db = DB.SQL(dbname)
    # 最高价格、最低价格
    # 取相应价位的手机
    phonelist = db.session.query(evalresult, phone_info).join(phone_info,
                                                              phone_info.productid == evalresult.productid).filter(
        and_(evalresult.price < maxp, evalresult.price > minp)).all()
    fcamerakey = []
    bcamerakey = []
    screenkey = []
    cpukey = []
    simkey = []
    brandkey = []
    weightkey = []
    thickkey = []
    fcameraref = {}
    bcameraref = {}
    screenref = {}
    cpuref = {}
    simref = {}
    brandref = {}
    weightref = {}
    thickref = {}
    for p in phonelist:
        print(p[1].brand, p[1].fpixel, p[1].bpixel)
    for p in phonelist:
        # 手机对象
        phone = p[0]
        # 参数对象
        info = p[1]
        if info.fpixel not in fcamerakey:  # 检测有多少种值
            fcamerakey.append(info.fpixel)
        if info.bpixel not in bcamerakey:
            bcamerakey.append(info.bpixel)
        if info.screen not in screenkey:
            screenkey.append(info.screen)
        if info.cpu not in cpukey:
            cpukey.append(info.cpu)
        if info.sim not in simkey:
            simkey.append(info.sim)
        if info.brand not in brandkey:
            brandkey.append(info.brand)
        if info.weight not in weightkey:
            weightkey.append(info.weight)
        if info.thick not in thickkey:
            thickkey.append(info.thick)

    for fcamera in fcamerakey:  # 初始化字典
        fcameraref.update({fcamera: 0})
    for bcamera in bcamerakey:
        bcameraref.update({bcamera: 0})
    for screen in screenkey:
        screenref.update({screen: 0})
    for cpu in cpukey:
        cpuref.update({cpu: 0})
    for sim in simkey:
        simref.update({sim: 0})
    for brand in brandkey:
        brandref.update({brand: 0})
    for weight in weightkey:
        weightref.update({weight: 0})
    for thick in thickkey:
        thickref.update({thick: 0})

    for p in phonelist:  # 得出每种值有多少台手机
        phone = p[0]
        info = p[1]

        # 计算时间差
        try:
            launch_year = int(info.year)
            launch_month = int(info.month)
            launch_date = datetime.datetime(launch_year, launch_month, 1)
            current_year = int(time.strftime('%Y', time.localtime(time.time())))
            current_month = int(time.strftime('%m', time.localtime(time.time())))
            current_date = datetime.datetime(current_year, current_month, 1)
            gap_days = (current_date - launch_date).days
            gap_months = gap_days / 30
            temp = phone.num
            num = temp / gap_months
        except:
            print('无上市时间')
            continue

        temp = fcameraref[info.fpixel]  # 取出字典中上一个值
        temp += num  # 加上当前值
        fcameraref.update({info.fpixel: temp})  # 回存字典

        temp = bcameraref[info.bpixel]
        temp += num
        bcameraref.update({info.bpixel: temp})

        temp = screenref[info.screen]
        temp += num
        screenref.update({info.screen: temp})

        temp = cpuref[info.cpu]
        temp += num
        cpuref.update({info.cpu: temp})

        temp = simref[info.sim]
        temp += num
        simref.update({info.sim: temp})

        temp = brandref[info.brand]
        temp += num
        brandref.update({info.brand: temp})

        temp = weightref[info.weight]
        temp += num
        weightref.update({info.weight: temp})

        temp = thickref[info.thick]
        temp += num
        thickref.update({info.thick: temp})

    fcamerakey.clear()
    sorted_fcameraref = sorted(fcameraref.items(), key=operator.itemgetter(1))
    for ref in sorted_fcameraref:
        fcamerakey.append(ref[0])

    bcamerakey.clear()
    sorted_bcameraref = sorted(bcameraref.items(), key=operator.itemgetter(1))
    for ref in sorted_bcameraref:
        bcamerakey.append(ref[0])

    screenkey.clear()
    sorted_screenref = sorted(screenref.items(), key=operator.itemgetter(1))
    for ref in sorted_screenref:
        screenkey.append(ref[0])

    cpukey.clear()
    sorted_cpuref = sorted(cpuref.items(), key=operator.itemgetter(1))
    for ref in sorted_cpuref:
        cpukey.append(ref[0])

    simkey.clear()
    sorted_simref = sorted(simref.items(), key=operator.itemgetter(1))
    for ref in sorted_simref:
        simkey.append(ref[0])

    brandkey.clear()
    sorted_brandref = sorted(brandref.items(), key=operator.itemgetter(1))
    for ref in sorted_brandref:
        brandkey.append(ref[0])

    weightkey.clear()
    sorted_weightref = sorted(weightref.items(), key=operator.itemgetter(1))
    for ref in sorted_weightref:
        weightkey.append(ref[0])

    thickkey.clear()
    sorted_thickref = sorted(thickref.items(), key=operator.itemgetter(1))
    for ref in sorted_thickref:
        thickkey.append(ref[0])

    # # 给每个手机打分再回存
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60
    phonelist = db.session.query(evalresult, phone_info).join(phone_info,
                                                              phone_info.productid == evalresult.productid).filter(
        evalresult.current_timeid == timeid).filter(
        and_(evalresult.price < maxp, evalresult.price > minp)).all()
    # 给每个手机打分再回存
    for p in phonelist:
        info = p[1]

        print(p[1].brand, db.session.query(products).filter(products.id == p[0].productid).first().name)
        # 总分、参数名、对应分值的字典
        score = 0
        scoreheader = []
        scoredic = {}

        for ref in fcamerakey:
            i = fcamerakey.index(ref)
            if ref == info.fpixel:
                scoreheader.append("fpixel")
                scoredic.update({"fpixel": 0})
                if i > 0.2 * len(sorted_fcameraref):
                    if i > 0.4 * len(sorted_fcameraref):
                        if i > 0.6 * len(sorted_fcameraref):
                            if i > 0.8 * len(sorted_fcameraref):
                                scoredic.update({"fpixel": 10})
                            else:
                                scoredic.update({"fpixel": 7})
                        else:
                            scoredic.update({"fpixel": 5})
                    else:
                        scoredic.update({"fpixel": 3})
                else:
                    scoredic.update({"fpixel": 1})
        # print(scoredic)

        for ref in bcamerakey:
            i = bcamerakey.index(ref)
            if ref == info.bpixel:
                scoreheader.append("bpixel")
                scoredic.update({"bpixel": 0})
                if i > 0.2 * len(sorted_bcameraref):
                    if i > 0.4 * len(sorted_bcameraref):
                        if i > 0.6 * len(sorted_bcameraref):
                            if i > 0.8 * len(sorted_bcameraref):
                                scoredic.update({"bpixel": 10})
                            else:
                                scoredic.update({"bpixel": 7})
                        else:
                            scoredic.update({"bpixel": 5})
                    else:
                        scoredic.update({"bpixel": 3})
                else:
                    scoredic.update({"bpixel": 1})

        for ref in screenkey:
            i = screenkey.index(ref)
            if ref == info.screen:
                scoreheader.append("screen")
                scoredic.update({"screen": 0})
                if i > 0.2 * len(sorted_screenref):
                    if i > 0.4 * len(sorted_screenref):
                        if i > 0.6 * len(sorted_screenref):
                            if i > 0.8 * len(sorted_screenref):
                                scoredic.update({"screen": 10})
                            else:
                                scoredic.update({"screen": 7})
                        else:
                            scoredic.update({"screen": 5})
                    else:
                        scoredic.update({"screen": 3})
                else:
                    scoredic.update({"screen": 1})

        for ref in cpukey:
            i = cpukey.index(ref)
            if ref == info.cpu:
                scoreheader.append("cpu")
                scoredic.update({"cpu": 0})
                if i > 0.2 * len(sorted_cpuref):
                    if i > 0.4 * len(sorted_cpuref):
                        if i > 0.6 * len(sorted_cpuref):
                            if i > 0.8 * len(sorted_cpuref):
                                scoredic.update({"cpu": 10})
                            else:
                                scoredic.update({"cpu": 7})
                        else:
                            scoredic.update({"cpu": 5})
                    else:
                        scoredic.update({"cpu": 3})
                else:
                    scoredic.update({"cpu": 1})

        for ref in simkey:
            i = simkey.index(ref)
            if ref == info.sim:
                scoreheader.append("sim")
                scoredic.update({"sim": 0})
                if i > 0.2 * len(sorted_simref):
                    if i > 0.4 * len(sorted_simref):
                        if i > 0.6 * len(sorted_simref):
                            if i > 0.8 * len(sorted_simref):
                                scoredic.update({"sim": 10})
                            else:
                                scoredic.update({"sim": 7})
                        else:
                            scoredic.update({"sim": 5})
                    else:
                        scoredic.update({"sim": 3})
                else:
                    scoredic.update({"sim": 1})

        for ref in brandkey:
            i = brandkey.index(ref)
            if ref == info.brand:
                scoreheader.append("brand")
                scoredic.update({"brand": 0})
                if i > 0.2 * len(sorted_brandref):
                    if i > 0.4 * len(sorted_brandref):
                        if i > 0.6 * len(sorted_brandref):
                            if i > 0.8 * len(sorted_brandref):
                                scoredic.update({"brand": 10})
                            else:
                                scoredic.update({"brand": 7})
                        else:
                            scoredic.update({"brand": 5})
                    else:
                        scoredic.update({"brand": 3})
                else:
                    scoredic.update({"brand": 1})

        for ref in weightkey:
            i = weightkey.index(ref)
            if ref == info.weight:
                scoreheader.append("weight")
                scoredic.update({"weight": 0})
                if i > 0.2 * len(sorted_weightref):
                    if i > 0.4 * len(sorted_weightref):
                        if i > 0.6 * len(sorted_weightref):
                            if i > 0.8 * len(sorted_weightref):
                                scoredic.update({"weight": 10})
                            else:
                                scoredic.update({"weight": 7})
                        else:
                            scoredic.update({"weight": 5})
                    else:
                        scoredic.update({"weight": 3})
                else:
                    scoredic.update({"weight": 1})

        for ref in thickkey:
            i = thickkey.index(ref)
            if ref == info.thick:
                scoreheader.append("thick")
                scoredic.update({"thick": 0})
                if i > 0.2 * len(sorted_thickref):
                    if i > 0.4 * len(sorted_thickref):
                        if i > 0.6 * len(sorted_thickref):
                            if i > 0.8 * len(sorted_thickref):
                                scoredic.update({"thick": 10})
                            else:
                                scoredic.update({"thick": 7})
                        else:
                            scoredic.update({"thick": 5})
                    else:
                        scoredic.update({"thick": 3})
                else:
                    scoredic.update({"thick": 1})
        for ref in scoreheader:
            score += scoredic[ref]
        print(score)

        # 存回的过程
        p[0].score = score
        detail = ""
        for h in scoreheader:
            detail = detail + h + "||" + str(scoredic[h]) + "||"
        p[0].score_detail = detail
        try:
            db.session.commit()
        except sqlalchemy.exc.DataError as ex:
            db.session.rollback()


# 训练神经网络预测手机受欢迎程度
def train_and_predic(dbname, minp, maxp):
    db = DB.SQL(dbname)

    # 时间戳
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60

    min = 10000
    # 取手机
    phonelist = db.session.query(evalresult, phone_info).join(phone_info, phone_info.productid == evalresult.productid).filter(
        evalresult.num > min).filter(
        and_(evalresult.price < maxp, evalresult.price > minp)).filter(evalresult.current_timeid==timeid).all()
    # phonelist = db.session.query(evalresult, phone_info).join(phone_info,
    #                                                           phone_info.productid == evalresult.productid).filter(
    #     evalresult.num > min).filter(evalresult.current_timeid == timeid).all()
    # 计算最大值 用于归一化
    fpixelmax = 1
    bpixelmax = 1
    screenmax = 1
    thickmax = 1
    weightmax = 1
    for p in phonelist:
        info = p[1]
        if info.fpixel > fpixelmax:
            fpixelmax = info.fpixel
        if info.bpixel > bpixelmax:
            bpixelmax = info.bpixel
        if info.screen > screenmax:
            screenmax = info.screen
        if info.thick > thickmax:
            thickmax = info.thick
        if info.weight > weightmax:
            weightmax = info.weight
    totalgoodrate = 0
    train = []
    ans = []
    for p in phonelist:
        totalgoodrate = totalgoodrate + p[0].goodrate
    avrGdRate = totalgoodrate / (len(phonelist) * 100)
    avrBdRate = 1 - avrGdRate
    print("rate " + str(avrGdRate))
    # TODO 生成训练集
    for p in phonelist:
        # if p[0].comm_eval == None:
        #     continue
        # 训练集
        t = []
        obj = db.session.query(products).filter(products.id == p[0].productid).first()
        print(obj.name)
        # 品牌列表
        brand = p[1].brand
        print(brand)
        if brand == None:
            brand = ''
        blist = []
        flg = 0
        for key in brandlist:
            check = re.search(key, brand)
            if check:
                blist.append(0.5)
                flg = 1
            else:
                blist.append(0)
        if flg == 0:
            blist.append(0.5)
        else:
            blist.append(0)
        t += blist

        t.append(p[1].fpixel / fpixelmax)
        t.append(1 - p[1].bpixel / bpixelmax)
        t.append(p[1].cpu / 5)
        t.append(1 - p[1].screen / screenmax)
        t.append(p[1].sim / 2)
        t.append(p[1].thick / thickmax)
        t.append(p[1].weight / weightmax)

        # 销量归一化(单位月销量*好评率)
        info = p[1]
        # 计算时间差
        try:
            launch_year = int(info.year)
            launch_month = int(info.month)
            launch_date = datetime.datetime(launch_year, launch_month, 1)
            current_year = int(time.strftime('%Y', time.localtime(time.time())))
            current_month = int(time.strftime('%m', time.localtime(time.time())))
            current_date = datetime.datetime(current_year, current_month, 1)
            gap_days = (current_date - launch_date).days
            gap_months = gap_days/30 +1
            # num_nor = p[0].num * p[0].comm_eval / 100 / gap_months
            num_nor = p[0].num * p[0].goodrate / 100 / gap_months
        except:
            print('无上市时间')
            continue
        print(num_nor)
        # 受欢迎程度打分 即答案
        if num_nor>100000: a=1
        elif num_nor>50000: a=0.7
        elif num_nor>10000:a=0.5
        elif num_nor>5000:a=0.3
        else: a=0.1
        train.append(t)
        ans.append(a)
    train = array(train)
    ans = array([ans]).T
    # print(train)
    # print(ans)
    # 训练
    neural_network = NeuralNetwork()
    neural_network.train(train, ans, 10000)

    # 存权重矩阵
    weightdic = ''
    list = neural_network.synaptic_weights
    print(list)
    for i in range(0, len(brandlist)):
        weightdic = weightdic + brandlist[i] + ':' + str(list[i][0]) + '||'
    i = len(brandlist)
    weightdic = weightdic + '其他品牌' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '前摄' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '后摄' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + 'cpu' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '屏幕' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + 'sim' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '厚度' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '重量' + ':' + str(list[i][0]) + '||'
    print(weightdic)
    obj = nnresult(timeid=timeid, weightdic=weightdic, fpixelmax=fpixelmax, bpixelmax=bpixelmax, screenmax=screenmax, thickmax=thickmax, weightmax=weightmax)
    try:
        db.session.add(obj)
        db.session.commit()
    except sqlalchemy.exc.DataError as ex:
        db.session.rollback()

    # 今日待分析
    list = db.session.query(evalresult, phone_info).join(phone_info,
                                                         phone_info.productid == evalresult.productid).filter(
        and_(evalresult.price < maxp, evalresult.price > minp)).filter(evalresult.current_timeid == timeid).all()

    for l in list:
        t = []
        # 品牌列表
        obj = db.session.query(products).filter(products.id == l[0].productid).first()
        print(obj.name)
        brand = l[1].brand
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

        t.append(l[1].fpixel / fpixelmax)
        t.append(1 - l[1].bpixel / bpixelmax)
        t.append(l[1].cpu / 5)
        t.append(1 - l[1].screen / screenmax)
        t.append(l[1].sim / 2)
        t.append(l[1].thick / thickmax)
        t.append(l[1].weight / weightmax)

        # 预测
        ans = neural_network.think(array(t))
        ans = int(np.round(ans, 2) * 100) / (1 - (minp / 10000))
        # 存回去
        print(l[0].productid, ':', ans, ':', l[0].num)
        l[0].exp_pop = ans
        try:
            db.session.commit()
        except sqlalchemy.exc.DataError as ex:
            db.session.rollback()
    db.close()

# 训练神经网络预测手机受欢迎程度
def train_and_predic_X(dbname):
    db = DB.SQL(dbname)
    Rst = []
    # 时间戳
    timeid = db.session.query(times).order_by(desc(times.id)).first().id

    min = 10000
    # 取手机
    phonelist = db.session.query(evalresult, phone_info).join(phone_info,
                                                              phone_info.productid == evalresult.productid).filter(
        evalresult.num > min).filter(evalresult.current_timeid == timeid).all()

    # 计算最大值 用于归一化
    fpixelmax = 1
    bpixelmax = 1
    screenmax = 1
    thickmax = 1
    weightmax = 1
    pricemax = 1
    for p in phonelist:
        info = p[1]
        if info.fpixel > fpixelmax:
            fpixelmax = info.fpixel
        if info.bpixel > bpixelmax:
            bpixelmax = info.bpixel
        if info.screen > screenmax:
            screenmax = info.screen
        if info.thick > thickmax:
            thickmax = info.thick
        if info.weight > weightmax:
            weightmax = info.weight
        price = p[0].price
        if price > pricemax:
            pricemax = price

    totalgoodrate = 0
    train = []
    ans = []
    ansfortrain = []
    for p in phonelist:
        totalgoodrate = totalgoodrate + p[0].goodrate
    avrGdRate = totalgoodrate / (len(phonelist) * 100)
    avrBdRate = 1 - avrGdRate
    print("rate " + str(avrGdRate))
    # TODO 生成训练集
    for p in phonelist:
        # if p[0].comm_eval == None:
        #     continue
        # 训练集
        t = []
        obj = db.session.query(products).filter(products.id == p[0].productid).first()
        print(obj.name)
        # 品牌列表
        brand = p[1].brand
        print(brand)
        if brand == None:
            brand = ''
        blist = []
        flg = 0
        for key in brandlist:
            check = re.search(key, brand)
            if check:
                blist.append(0.5)
                flg = 1
            else:
                blist.append(0)
        if flg == 0:
            blist.append(0.5)
        else:
            blist.append(0)
        t += blist

        t.append(p[1].fpixel / fpixelmax)
        t.append(p[1].bpixel / bpixelmax)
        t.append(p[1].cpu / 5)
        t.append(p[1].screen / screenmax)
        t.append(p[1].sim / 2)
        t.append(p[1].thick / thickmax)
        t.append(p[1].weight / weightmax)
        t.append(p[0].price / pricemax)
        train.append(t)
        # 销量归一化(单位月销量*好评率)
        info = p[1]

        # 计算时间差
        try:
            launch_year = int(info.year)
            launch_month = int(info.month)
            launch_date = datetime.datetime(launch_year, launch_month, 1)
            current_year = int(time.strftime('%Y', time.localtime(time.time())))
            current_month = int(time.strftime('%m', time.localtime(time.time())))
            current_date = datetime.datetime(current_year, current_month, 1)
            gap_days = (current_date - launch_date).days
            gap_months = gap_days / 30 + 1
            # num_nor = p[0].num * p[0].comm_eval / 100 / gap_months
            # num_nor = p[0].num * p[0].goodrate / 100 / gap_months

        except:
            print('无上市时间')
            continue

    for p in phonelist:
        result = -p[0].num * (1 - p[0].goodrate / 100 - avrBdRate) / gap_months
        Rst.append(result)
        # 数据标准化
    Rst.sort()
    minvalue = Rst[0]
    maxvalue = Rst[-1]
    # print(Rst)
    for p in phonelist:
        result = -p[0].num * (1 - p[0].goodrate / 100 - avrBdRate) / gap_months
        stadardizedResult = 10 * ((result - minvalue) / (maxvalue - minvalue))

        if stadardizedResult == 0.0:
            stadardizedResult = 5.00

        ans.append(stadardizedResult / 100)
    train = array(train)
    print(train)
    ans = array([ans]).T

    print(ans)

    # 训练
    neural_network = NeuralNetwork()

    neural_network.train(train, ans, 100)
    print(neural_network.synaptic_weights)

    # 存权重矩阵
    weightdic = ''
    list = neural_network.synaptic_weights

    for i in range(0, len(brandlist)):
        weightdic = weightdic + brandlist[i] + ':' + str(list[i][0]) + '||'
    i = len(brandlist)
    weightdic = weightdic + '其他品牌' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '前摄' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '后摄' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + 'cpu' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '屏幕' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + 'sim' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '厚度' + ':' + str(list[i][0]) + '||';
    i += 1
    weightdic = weightdic + '重量' + ':' + str(list[i][0]) + '||'

    obj = nnresult(timeid=timeid, weightdic=weightdic, fpixelmax=fpixelmax, bpixelmax=bpixelmax, screenmax=screenmax, thickmax=thickmax, weightmax=weightmax , pricemax=pricemax)
    try:
        db.session.add(obj)
        db.session.commit()
    except sqlalchemy.exc.DataError as ex:
        db.session.rollback()

    # 今日待分析
    list = db.session.query(evalresult, phone_info).join(phone_info,
                                                         phone_info.productid == evalresult.productid).filter(
        evalresult.num > min).filter(evalresult.current_timeid == timeid).all()

    Think = []
    for l in list:
        t = []
        # 品牌列表
        obj = db.session.query(products).filter(products.id == l[0].productid).first()
        # print(obj.name)
        brand = l[1].brand
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

        t.append(l[1].fpixel / fpixelmax)
        t.append(l[1].bpixel / bpixelmax)
        t.append(l[1].cpu / 5)
        t.append(l[1].screen / screenmax)
        t.append(l[1].sim / 2)
        t.append(l[1].thick / thickmax)
        t.append(l[1].weight / weightmax)
        t.append(l[0].price / pricemax)

        ans = neural_network.think(array(t))
        ans[0] = ans[0] * l[0].price *10000000
        print(l[0].productid, db.session.query(products).filter(products.id == l[0].productid).first().name, ' ', ans[0])
        l[0].exp_pop = int(ans[0])
        try:
            db.session.commit()
        except sqlalchemy.exc.DataError as ex:
            db.session.rollback()
    db.close()

def check():
    db = DB.SQL('datadb')

    # 时间戳
    timeid = db.session.query(times).order_by(desc(times.id)).first().id
    # timeid = 60
    # 今日待分析
    list = db.session.query(evalresult, products, stores, phone_info).join(products,
                                                                           products.id == evalresult.productid).join(
        stores, stores.id == evalresult.storeid).join(phone_info, phone_info.productid == evalresult.productid).filter(
        evalresult.current_timeid == timeid).filter(evalresult.platformid == 4).order_by(
        desc(evalresult.num)).all()
    i = 0

    for l in list:
        i += 1
        print(str(i) + ' | ' + str(l[0].platformid) + '\t' + str(l[0].num) + '\t' + str(l[0].data_timeid) + ' \t' + l[
            1].name + '\t\t ' + str(
            l[0].price) + '\t ' + str(l[0].score) + '\t ' + str(l[0].exp_pop) + '\t ' + str(l[0].comm_eval) + '\t '+ l[2].name + ' '+ str(l[3].year))
    db.close()


# info = num.info  # 取出此价位中手机的信息， 是一个String
# fragment = info.split(",")  # 以，为分隔符分割，存入fragment列表中
# phone_info = phone_info()

# mysqldump datadb -u thx -pthx --add-drop-table | mysql testdb -u thx -pthx

if __name__ == '__main__':
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"

    logging.basicConfig(filename='eval.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    #
    getscore('datadb', 10000, 100000)
    getscore('datadb', 6000, 10000)
    getscore('datadb', 4000, 6000)
    getscore('datadb', 3000, 4000)
    getscore('datadb', 2000, 3000)
    getscore('datadb', 1000, 2000)
    getscore('datadb', 0, 1000)

    train_and_predic('datadb', 6000, 100000)
    train_and_predic('datadb', 4000, 6000)
    train_and_predic('datadb', 2500, 4000)
    train_and_predic('datadb', 1500, 2500)
    train_and_predic('datadb', 0, 1500)

    # train_and_predic_X('datadb')

    check()

    evalation('datadb')
