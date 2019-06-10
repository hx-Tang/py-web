# -*-coding:utf-8-*-
import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import os
import sys
import io
import time
from collections import OrderedDict
import datetime
import random
import logging
import SQL
import urllib3

# 代理池
Proxies = []
# 代理池key
Key = '20190328154951525'


def getproxys():
    global Proxies
    global Key
    while len(Proxies) == 0:
        # 一次获取50个代理ip
        # print('请求代理'+ str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        url = 'http://dec.ip3366.net/api/?key=' + Key + '&getnum=50&area=1&proxytype=1'
        try:
            r = requests.get(url)
        except:
            print('代理ip获取失败')
            time.sleep(5)
            continue
        try:
            Proxies += r.text.split('\r\n')
            Proxies.remove('')
        except:
            r.encoding = r.apparent_encoding
            print(r.text)
            Proxies.pop()
            time.sleep(5)
            continue
        # # 验证代理有效性
        # print('测试可用代理：\r')
        # tmp = Proxies[:]
        # for prox in tmp:
        #     try:
        #         requests.get('https://www.baidu.com/', proxies={"https": prox}, timeout=1)
        #         print(prox)
        #     except:
        #         print(prox + '无效')
        #         Proxies.remove(prox)
    return random.choice(Proxies)


# 通过URL获取网页文本
def getHtmlText(url):
    global Proxies
    while 1:
        prox = getproxys()
        try:
            proxies = {'https': prox}
            r = requests.get(url, proxies=proxies, timeout=0.5)
            print(prox + ' -> '+url)
            r.encoding = r.apparent_encoding
            if r.text == '':
                print(prox + 'ip被封更换ip')
                Proxies.remove(prox)
                continue
            return r.text
        except:
            # print(prox + "ip超时")
            Proxies.remove(prox)
            continue


# 生成手机1-100页的url列表
def getAllPages():
    allPagesUrlList = []
    for page in range(0, 5):
        singlePageUrl = 'https://list.suning.com/0-20006-' + str(page) + '.html'
        allPagesUrlList.append(singlePageUrl)
    return allPagesUrlList


# 在手机概览界面网页获取手机详细信息链接的列表
def getPhonesUrl(pageUrl):
    phonesUrlList = []
    html = requests.get(pageUrl).text
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all(class_="img-block")
    for item in items:
        phonesUrlList.append('https:' + item.a.get('href'))

    for i in range(0, 5):
        url = 'https://list.suning.com/emall/searchV1Product.do?ci=20006&pg=03&cp=' + str(
            page) + '&il=0&iy=0&n=1&sesab=ACBAAB&id=IDENTIFYING&cc=010&paging=' + str(i) + '&sub=1&jzq=15724'
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'lxml')
        items = soup.find_all(class_="img-block")
    for item in items:
        phonesUrlList.append('https:' + item.a.get('href'))
    return phonesUrlList


# 获取手机名称
def getPhoneName(phoneurl):
    html = getHtmlText(phoneurl)
    pattern4 = re.compile('"itemDisplayName":"(.*?)",')
    itemDisplayName = re.findall(pattern4, html)[0]
    if '/' in itemDisplayName:
        itemDisplayName = itemDisplayName.replace('/', ' ')
    return itemDisplayName[0:50]


# 获取手机ID
def getPhoneID(phoneurl):
    phoneID = phoneurl[38:-5]
    return phoneID


# 获取爬虫日期
def getDate():
    today = datetime.date.today()
    str1 = str(today)
    return str1


def getShopName():
    html = getHtmlText(phoneurl)

    pattern0 = re.compile('"flagshipName":"(.*?)",')
    shopname = re.findall(pattern0, html)[0]  # 商店名称
    return shopname[0:19]


# 获取店铺ID
def getShopID():
    html = getHtmlText(phoneurl)
    pattern00 = re.compile('"flagshipid":"(.*?)",')  # 商店id
    shop_id = re.findall(pattern00, html)[0]

    return shop_id


# 获取手机价格
def getPhonePrice(phoneurl):
    id = getPhoneID(phoneurl)
    b = ''
    for i in range(18 - len(id)):
        b = b + '0'

    priceUrl1 = 'https://icps.suning.com/icps-web/getAllPriceFourPageV1/' + b + id + '_010_0100101_1_' + phoneurl[
                                                                                                         27:37] + '__pds_FourPage.getHisPrice.jsonp?callback=FourPage.getHisPrice'
    response1 = requests.get(priceUrl1)  # 获取价格
    pattern1 = re.compile('"netPrice":"(.*?)"')
    price = re.findall(pattern1, response1.text)[0]
    if price == "":
        return 0
    return price


# 获取手机图片链接
def getPhoneImages(phoneurl):
    id = getPhoneID(phoneurl)
    b = ''
    for i in range(18 - len(id)):
        b = b + '0'
    phoneImageLink = 'https://image1.suning.cn/uimg/b2c/newcatentries/0000000000-' + b + id + '_1_680x680.jpg'

    return phoneImageLink


# 获取该买该手机的评论信息
def getPhoneComments(phoneurl):
    id = phoneurl[38:-5]
    b = ''
    for i in range(18 - len(id)):
        b = b + '0'
    reviewUrl = 'https://review.suning.com/ajax/review_count/general--' + b + id + '-' + phoneurl[
                                                                                         27:37] + '-----satisfy.htm?callback=satisfy'

    htmlText = getHtmlText(reviewUrl)

    try:

        try:
            jsonText = json.loads(htmlText[25:-58])

        # print(jsonText)
        except:
            print('ex')
            return {'0', '0', '0', '0', '0', '0', '0'}, []

        # 手机评价信息概览
        commentSummaryDict = {}
        commentSummary = jsonText
        commentSummaryDict.update({'好评率': commentSummary['qualityStar']})
        commentSummaryDict.update({'评论数': commentSummary['totalCount']})
        commentSummaryDict.update({'晒图': commentSummary['picFlagCount']})
        commentSummaryDict.update({'追评数': commentSummary['againCount']})
        commentSummaryDict.update({'好评数': commentSummary['fiveStarCount']})
        commentSummaryDict.update({'中评数': commentSummary['threeStarCount']})
        commentSummaryDict.update({'差评数': commentSummary['oneStarCount']})
    # print(commentSummaryDict)
    except Exception as e:
        print('b')

    # 获取前50页的评价内容
    try:
        userCommentList = []
        for commentPage in range(0, 10):
            html = getHtmlText(phoneurl)
            pattern = re.compile('"clusterId":"(.*?)"')  # 爬取clusterId，只有有了clusterId才能爬取每个手机的评价内容
            ClusterId = re.findall(pattern, html)[0]
            id = phoneurl[38:-5]
            b = ''
            for i in range(18 - len(id)):
                b = b + '0'
            generalCommentUrl = 'https://review.suning.com/ajax/cluster_review_lists/general-' + str(
                ClusterId) + '-' + b + id + '-' + phoneurl[27:37] + '-total-' + str(
                commentPage + 1) + '-default-10-----reviewList.htm?callback=reviewList'
            ResponseGeneral = requests.get(generalCommentUrl).text
            patternGeneral = re.compile('"content":"(.*?)"')
            CommentGeneral = re.findall(patternGeneral, ResponseGeneral)
            packageCommentUrl = 'https://review.suning.com/ajax/cluster_review_lists/package--' + b + id + '-0000000000-total-' + str(
                commentPage + 1) + '-default-10-----reviewList.htm?callback=reviewList'
            ResponsePackage = requests.get(packageCommentUrl).text
            patternPackage = re.compile('"content":"(.*?)"')
            CommentPackage = re.findall(patternPackage, ResponsePackage)

            if len(CommentGeneral) == 0 and not len(CommentPackage) == 0:
                commentUrl = packageCommentUrl
            elif len(CommentPackage) == 0 and not len(CommentGeneral) == 0:
                commentUrl = generalCommentUrl

            commentHtmlText = getHtmlText(commentUrl)

            try:
                pattern0 = re.compile('"nickName":"(.*?)",')
                nickName = re.findall(pattern0, commentHtmlText)
                pattern00 = re.compile('"levelName":"(.*?)",')
                LevelName = re.findall(pattern00, commentHtmlText)
                pattern01 = re.compile('"qualityStar":"(.*?)",')
                qualityStar = re.findall(pattern01, commentHtmlText)
                pattern02 = re.compile('"content":"(.*?)",')
                content = re.findall(pattern02, commentHtmlText)
                pattern03 = re.compile('"commodityName":"(.*?)",')
                commodityName = re.findall(pattern03, commentHtmlText)
                pattern04 = re.compile('"publishTimeStr":"(.*?)",')
                publishTimeStr = re.findall(pattern04, commentHtmlText)
                pattern05 = re.compile('"sourceSystem":"(.*?)",')
                sourceSystem = re.findall(pattern05, commentHtmlText)

                commentsInfo = {}
                for a in nickName:
                    commentsInfo.update({'昵称': a})
                for b in LevelName:
                    commentsInfo.update({'用户等级': b})

                commentsInfo.update({'评论星级':' ' })
                for d in content:
                    commentsInfo.update({'内容': d})
                for e in commodityName:
                    commentsInfo.update({'机型': e[0:49]})
                for f in publishTimeStr:
                    commentsInfo.update({'发表时间': f})
                commentsInfo.update({'点赞数': 0})
                commentsInfo.update({'评论回复次数': 0})
                commentsInfo.update({'是否推荐': 0})
                for g in sourceSystem:
                    commentsInfo.update({'客户端': g})
                userCommentList.append(commentsInfo)
                # print(userCommentList)
            except Exception as e:
                print(e)

            print('******正在爬取第' + str(commentPage + 1) + '页评论\r')
            logging.info('******正在爬取第' + str(commentPage + 1) + '页评论\r')
    except Exception as e:
        print(e)

    return commentSummaryDict, userCommentList


# 获取手机的属性信息
def getPhoneProperties(phoneurl):
    phoneProperties = {}
    list_value = []
    list_name = []
    html = getHtmlText(phoneurl)
    soup = BeautifulSoup(html, 'lxml')
    values = soup.find_all(class_='val')
    for value in values:
        list_value.append(value.string)
    #names = soup.select('td div span')
    del(list_value[0])
    pattern = re.compile(' <div class="name-inner"> <span>(.*?)</span>')
    list_name = re.findall(pattern, html)
    #print(list_name)


    for i in range(0, len(list_name)):
        phoneProperties.update({list_name[i]: list_value[i]})

    return phoneProperties


# 将手机的特征添加到一起
def getPhoneInfo(phoneurl):
    phoneInfo = {}
    phoneInfo.update({'平台': "苏宁"})

    date = getDate()
    phoneInfo.update({'爬虫日期': date})

    phoneID = getPhoneID(phoneurl)
    phoneInfo.update({'商品ID': phoneID})

    shopID = getShopID()
    phoneInfo.update({'店铺ID': shopID})

    price = getPhonePrice(phoneurl)
    phoneInfo.update({'价格': price})

    name = getPhoneName(phoneurl)
    phoneInfo.update({'名称': name})

    phoneImageLink = getPhoneImages(phoneurl)
    phoneInfo.update({'图片链接': phoneImageLink})

    phoneProperties = getPhoneProperties(phoneurl)
    phoneInfo.update({'手机配置': phoneProperties})

    shopname = getShopName()
    phoneInfo.update({'店铺名称': shopname})

    commentSummaryDict, userCommentList = getPhoneComments(phoneurl)
    phoneInfo.update({'手机整体评价': commentSummaryDict})
    phoneInfo.update({'手机全部评价内容': userCommentList})

    return phoneInfo


# 检查重复性
def check(SQL, timeid, phoneurl):
    if SQL.check([timeid, getPhoneID(phoneurl)]):
        return 1
    return 0

def checkd():
    phoneProperties = getPhoneProperties('')
    Pro = ''
    for key in phoneProperties.keys():
        Pro = Pro + ',' + key + ',' + phoneProperties[key]

if __name__ == '__main__':

    urllib3.disable_warnings()

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"

    logging.basicConfig(filename='SNlog.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    # 程序开始时间
    startTime = time.process_time()

    # 获取代理ip
    getproxys()

    # 连接SQL
    SQL = SQL.SQL('datadb')
    # SQL = SQL.SQL('testdb')

    # 获取平台id
    platformid = SQL.query_id('platforms', ['SN'])

    # 获取时间戳及时间id
    current_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    timeid = SQL.insert('times', [current_date])

    logging.info('\r 爬虫开始 \r')
    print("SN爬虫开始" + str(current_date) + '\r')

    for page in range(0, 10):
        print('----------正在爬取第' + str(page + 1) + '页手机\r')

        urlList = getAllPages()
        url = urlList[page]

        # today = datetime.date.today()
        # t = 'JingDong ' + str(today) + '/'
        # rootPath = os.path.join('/Users', 'apple-1', t)  # 添加路径

        # phoneInfoAll = []
        phoneUrls = getPhonesUrl(url)

        for phoneurl in phoneUrls:
            print('正在爬取第', str(phoneUrls.index(phoneurl) + 1), '部手机......\r')
            logging.info('正在爬取第' + str(phoneUrls.index(phoneurl) + 1) + '部手机......\r')

            # 查重
            if check(SQL, timeid, phoneurl):
                print("重复爬取\r")
                logging.info('重复爬取\r')
                continue

            # 爬数据
            try:
                info = getPhoneInfo(phoneurl)
                # print(info)
            except Exception as e:
                print("出错跳过\r")
                print(e)
                logging.info('出错跳过\r')


            try:
                # 存产品编号 获得主键
                productid = SQL.insert('products', [info['商品ID'], platformid, info['名称']])

                # 存店铺编号 获得主键
                storeid = SQL.insert('stores', [info['店铺ID'], platformid, info['店铺名称'], "自营"])
            except Exception as e:
                print(e)
                print('出错跳过')
                SQL.session.rollback()
                continue

            print(info['价格'])
            # 存单条爬虫数据 获得主键
            try:
                datalist = [productid, timeid, platformid, storeid, info['价格'], info['手机整体评价']['好评率'],
                            info['手机整体评价']['评论数'], info['手机整体评价']['晒图'], info['手机整体评价']['追评数'],
                            info['手机整体评价']['好评数'], info['手机整体评价']['中评数'], info['手机整体评价']['差评数']]
            except TypeError as ex:
                print(ex)
                continue
                # datalist = [productid, timeid, platformid, storeid, info['价格']]
            except:
                continue

            pid = SQL.insert('phones', datalist)
            print(pid)

            # 重复爬取则跳过
            if pid == -1:
                print("重复爬取\r")
                logging.info('重复爬取\r')
                continue

            # 下载并存图片
            phoneImaLink = info['图片链接']
            try:
                imgHtml = requests.get(phoneImaLink, stream=True, headers={
                    'User-Agent': 'User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari'
                                  '/537.36 SE 2.X MetaSr 1.0'})
            except Exception as e:
                print(e)
            else:
                imgHtml.encoding = imgHtml.apparent_encoding
                SQL.insert('imgs', [pid, imgHtml.content])

            # 存配置信息
            phoneProperties = info['手机配置']
            Pro = ',包装清单'
            for key in phoneProperties.keys():
                Pro = Pro + '||' + key + '||' + phoneProperties[key]
            SQL.insert('raw_info', [pid, Pro])

            # 存评论
            commentsHeader = ['昵称', '用户等级', '评论星级', '内容', '机型', '发表时间', '点赞数', '评论回复次数',
                              '是否推荐', '客户端']
            userCommentList = info['手机全部评价内容']

            for comment in userCommentList:
                try:
                    tempList = [pid]
                    for commentInfo in commentsHeader:
                        tempList.append(comment[commentInfo])
                    SQL.insert('comments', tempList)
                except Exception as e:
                    print(e)
                    continue

    # 关闭SQL连接
    SQL.close()

    # 程序结束时间
    endTime = time.process_time()
    print('所有手机爬取完毕,程序耗费的时间为：', endTime - startTime)
    logging.info('所有手机爬取完毕,程序耗费的时间为：' + str(endTime - startTime) + '\r')
