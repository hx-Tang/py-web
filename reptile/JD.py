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
# from Util import SQL
import SQL
from SQL import comm_img
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
        url = 'http://ged.ip3366.net/api/?key=' + Key + '&getnum=50&area=1&proxytype=1'
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
def getHtmlText(url,flg =0,id = 0):
    global Proxies
    while 1:
        prox = getproxys()
        try:
            if flg == 1:
                #id=getPhoneID(phoneurl)
                proxies = {'https': prox}
                headers={'Accept': '*/*',
                'Accept-Encoding': 'br, gzip, deflate',
                'Host': 'sclub.jd.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
                'Accept-Language': 'zh-cn',
                'Referer': 'https://item.jd.com/'+id+'.html',
                'Connection': 'keep-alive'}
                r = requests.get(url, proxies=proxies, headers=headers,timeout=0.5)
            else:
                proxies = {'https': prox}
                r = requests.get(url, proxies=proxies, timeout=0.5)
                # r = requests.get(url, timeout=0.5)
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
    for page in range(0, 100):
        singlePageUrl = 'https://list.jd.com/list.html?cat=9987,653,655&page=' \
                        + str(page) + '&sort=sort%5Frank%5Fasc&trans=1&JL=6_0_0#J_main'
        allPagesUrlList.append(singlePageUrl)
    return allPagesUrlList


# 在手机概览界面网页获取手机详细信息链接的列表
def getPhonesUrl(pageUrl):
    phonesUrlList = []
    html = getHtmlText(pageUrl,0,0)
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', attrs={'class': 'p-name'})
    for item in items:
        phonesUrlList.append('https:' + item.a.get('href'))
    return phonesUrlList


# 获取手机名称
def getPhoneName(phoneurl):
    infoText = getHtmlText(phoneurl,0,0)
    soup = BeautifulSoup(infoText, 'html.parser')
    name = soup.find('div', attrs={'class': 'item ellipsis'}).get_text().strip()
    return name[0:69]


# 获取手机ID
def getPhoneID(phoneurl):
    phoneID = phoneurl[20:-5]
    return phoneID


# 获取爬虫日期
def getDate():
    today = datetime.date.today()
    str1 = str(today)
    return str1


def getShopName():
    infoText = getHtmlText(phoneurl)
    soup = BeautifulSoup(infoText, 'html.parser')
    shopname = soup.find('a', attrs={'clstag': 'shangpin|keycount|product|dianpuname1'}).get_text().strip()
    return shopname[0:19]


def getShopTag():
    infoText = getHtmlText(phoneurl)
    soup = BeautifulSoup(infoText, 'html.parser')
    shoptag = soup.find('div', attrs={'class': 'name goodshop EDropdown'}).get_text().strip()
    if (shoptag == ''):
        shoptag = "非自营"
    return shoptag


# 获取店铺ID
def getShopID():
    response = getHtmlText(phoneurl)
    ids = re.findall(r"venderId:(.*?),\s.*?shopId:'(.*?)'", response)
    if not ids:
        ids = re.findall(r"venderId:(.*?),\s.*?shopId:(.*?),", response)
    # vender_id = ids[0][0]# 卖家ID
    shop_id = ids[0][1]
    return shop_id


# 获取手机价格
def getPhonePrice(phoneurl):
    # 由于价格不在主页面显示，通过抓包找到显示价格的网址，以物品编号为区别特征
    priceUrl = 'https://p.3.cn/prices/mgets?pduid=' + str(random.randint(100000, 999999)) + '&skuIds=J_' + phoneurl[
                                                                                                           20:-5]
    priceText = getHtmlText(priceUrl)
    pattern = re.compile('"p":"(.*?)"')
    price = re.findall(pattern, priceText)[0]
    return price


# 获取手机图片链接（小图）
def getPhoneImages(phoneurl):
    infoText = getHtmlText(phoneurl)
    #print(infoText)
    soup = BeautifulSoup(infoText, 'html.parser')
    #print(soup)
    imgDiv = soup.find('div', attrs={'class': 'spec-items'})
    #print(imgDiv)
    phoneImageLink = []
    for img in imgDiv.findAll('img'):
        phoneImageLink.append('https:' + img.get('src'))
        #print(('https:' + img.get('src')))

    soupB = BeautifulSoup(infoText, 'html.parser')
    imgDivB = soupB.find('div', attrs={'class': 'jqzoom main-img','id':'spec-n1'})
    #print(imgDivB)
    phoneImageLinkB = []
    for imgB in imgDivB.findAll('img'):
        phoneImageLinkB.append('https:' + imgB.get('data-origin'))
        #print(('https:' + imgB.get('src')))

    #print(phoneImageLink)
    #print(phoneImageLinkB)
    return phoneImageLink,phoneImageLinkB



# 获取店铺类型
def getShopType(phoneurl):
    infoText = getHtmlText(phoneurl)
    soup = BeautifulSoup(infoText, 'html.parser')
    shoptype = soup.find('div', attrs={'class': 'name goodshop EDropdown'}).get_text().strip()
    if (shoptype == ''):
        shoptype = "非自营"
    return shoptype


# 将网页原生的是否推荐的True和False替换为是和否
def changeRecommnedType(inputBool):
    if inputBool == True:
        return '是'
    else:
        return '否'


# 获取该买该手机的评论信息
def getPhoneComments(phoneurl):
    def num_parse(num):
        tmp = str(num)
        num = float(re.findall(r"\d+\.?\d*", str(num))[0])
        for letter in tmp:
            if letter == '万':
                num = num * 10000
        return num

    phoneId = phoneurl[20:-5]
    commentStartUrl = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv789&productId=' + phoneId + \
                      '&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
    htmlText = getHtmlText(commentStartUrl,1,phoneId)
    #print(htmlText)


    try:
        # print(htmlText[25:-2])
        htmlText = htmlText.replace("\\", "'");
        jsonText = json.loads(htmlText[25:-2])
        #jsonText = jsonText.replace("'''''", "\\");

        #print(jsonText)
    except Exception as ex:
         print(ex)
         #print("111111111111111111111")
         return {'0', '0', '0', '0', '0', '0', '0'}, []

    # 手机评价信息概览
    commentSummaryDict = {}
    commentSummary = jsonText['productCommentSummary']
    commentSummaryDict.update({'好评率': num_parse(commentSummary['goodRateShow'])})
    commentSummaryDict.update({'评论数': num_parse(commentSummary['commentCountStr'])})
    commentSummaryDict.update({'晒图': jsonText['imageListCount']})
    commentSummaryDict.update({'追评数': num_parse(commentSummary['afterCountStr'])})
    commentSummaryDict.update({'好评数': num_parse(commentSummary['goodCountStr'])})
    commentSummaryDict.update({'中评数': num_parse(commentSummary['generalCountStr'])})
    commentSummaryDict.update({'差评数': num_parse(commentSummary['poorCountStr'])})
    #print(commentSummaryDict)

    # 获取前10页的评价内容
    userCommentList = []
    for commentPage in range(0, 10):
        # #commentPageUrl= 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv4314&productId=100002962227&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1'
        # commentPageUrl = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv4314&productId=' + phoneId + \
        #                  '&score=0&sortType=5&page=' + str(commentPage) + '&pageSize=10&isShadowSku=0&fold=1'
        commentPageUrl = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv789&productId=' + phoneId + '&score=0&sortType=5&' \
                                                                             'page=' + str(commentPage) + '&pageSize=10&isShadowSku=0&fold=1'
        commentHtmlText = getHtmlText(commentPageUrl, 1, phoneId)

        # 评论可多可少，出错就直接跳过
        try:
            commentHtmlText = commentHtmlText.replace("\\", "'");
            commentJsonText = json.loads(commentHtmlText[25:-2])
            comments = commentJsonText['comments']
            print('******************')
            print(comments)
            for comment in comments:
                commentsInfo = {}
                commentsInfo.update({'昵称': comment['nickname']})
                commentsInfo.update({'用户等级': comment['userLevelName']})
                commentsInfo.update({'评论星级': str(comment['score']) + '星'})
                commentsInfo.update({'内容': comment['content']})
                commentsInfo.update({'机型': comment['productColor'] + ',' + comment['productSize']})
                commentsInfo.update({'发表时间': comment['creationTime']})
                commentsInfo.update({'点赞数': comment['usefulVoteCount']})
                commentsInfo.update({'评论回复次数': comment['replyCount']})
                commentsInfo.update({'是否推荐': comment['recommend']})
                commentsInfo.update({'客户端': comment['userClientShow']})

                userCommentList.append(commentsInfo)
                #print(userCommentList)
        except TypeError as ex:
            print(ex)
            continue
        except:
            continue
        print('******正在爬取第' + str(commentPage + 1) + '页评论\r')
        logging.info('******正在爬取第' + str(commentPage + 1) + '页评论\r')

    return commentSummaryDict, userCommentList


# 获取手机的属性信息
def getPhoneProperties(phoneurl):
    phoneProperties = {}
    list_value = []
    list_name = []

    infoText = getHtmlText(phoneurl)
    soup = BeautifulSoup(infoText, 'html.parser')
    proSection = soup.findAll('div', attrs={'class': 'Ptable-item'})

    for pro in proSection:
        # 既然找不到直接去除有属性标签的方法就取个差集吧
        list_all = pro.find_all('dd')
        list_extracted = pro.find_all('dd', {'class': 'Ptable-tips'})
        list_chosen = [i for i in list_all if i not in list_extracted]

        for dd in list_chosen:
            list_value.append(dd.string)

        for dt in pro.find_all('dt'):
            list_name.append(dt.string)

    for i in range(0, len(list_name)):
        phoneProperties.update({list_name[i]: list_value[i]})

    return phoneProperties


# 将手机的特征添加到一起
def getPhoneInfo(phoneurl):

    phoneInfo = {}
    phoneInfo.update({'平台': "淘宝"})

    date = getDate()
    #print("1"+ date)
    phoneInfo.update({'爬虫日期': date})

    phoneID = getPhoneID(phoneurl)
    #print("2"+ phoneID)
    phoneInfo.update({'商品ID': phoneID})

    shopID = getShopID()
    #print("3"+ shopID)
    phoneInfo.update({'店铺ID': shopID})

    price = getPhonePrice(phoneurl)
    #print("4"+ price)
    phoneInfo.update({'价格': price})

    name = getPhoneName(phoneurl)
    #print("5"+ name)
    phoneInfo.update({'名称': name})

    phoneImageLink,phoneImageLinkB = getPhoneImages(phoneurl)
    phoneInfo.update({'小图片链接': phoneImageLink})
    #print(phoneImageLink)
    phoneInfo.update({'大图片链接': phoneImageLinkB})
    #print(phoneImageLinkB)

    phoneProperties = getPhoneProperties(phoneurl)
    phoneInfo.update({'手机配置': phoneProperties})

    shopname = getShopName()
    phoneInfo.update({'店铺名称': shopname})

    shoptype = getShopType(phoneurl)
    phoneInfo.update({'店铺类型': shoptype})

    shoptag = getShopTag()
    phoneInfo.update({'店铺标签': shoptag})

    commentSummaryDict, userCommentList = getPhoneComments(phoneurl)
    phoneInfo.update({'手机整体评价': commentSummaryDict})
    phoneInfo.update({'手机全部评价内容': userCommentList})

    return phoneInfo


# 检查重复性
def check(SQL, timeid, phoneurl):
    if SQL.check([timeid, getPhoneID(phoneurl)]):
        return 1
    return 0

def t():
    phoneProperties = getPhoneProperties('https://item.jd.com/10973073407.html')
    Pro = ''
    for key in phoneProperties.keys():
        Pro = Pro + ',' + key + ',' + phoneProperties[key]
    print(Pro)

def t2():
    phoneUrls = getPhonesUrl()

if __name__ == '__main__':

    urllib3.disable_warnings()

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"

    logging.basicConfig(filename='JDlog.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    # 程序开始时间
    startTime = time.process_time()

    # 获取代理ip
    getproxys()

    # 连接SQL
    # SQL = SQL.SQL('datadb')
    SQL = SQL.SQL('datadb')

    # 获取平台id
    platformid = SQL.query_id('platforms', ['JD'])

    # 获取时间戳及时间id
    current_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    timeid = SQL.insert('times', [current_date])



    logging.info('\r 爬虫开始 \r')
    print("爬虫开始" + str(current_date) + '\r')

    for page in range(0, 10):
        print('----------正在爬取第' + str(page + 1) + '页手机\r')
        logging.info('----------正在爬取第' + str(page + 1) + '页手机\r')
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
            #print('***********')
            #getPhoneComments(phoneurl)

            # 查重
            if check(SQL, timeid, phoneurl):
                print("重复爬取\r")
                logging.info('重复爬取\r')
                continue

            # 爬数据
            try:
                info = getPhoneInfo(phoneurl)
            except Exception as ex:
                 print(ex)
                 print("出错跳过\r")
                 logging.info('出错跳过\r')
                 continue

            # 存产品编号 获得主键
            try:
                productid = SQL.insert('products', [info['商品ID'], platformid, info['名称']])
            except:
                print('数据库出错')
                continue

            # 存店铺编号 获得主键
            storeid = SQL.insert('stores', [info['店铺ID'], platformid, info['店铺名称'], info['店铺类型']])
            # storeid = SQL.insert('stores', [info['店铺ID'], platformid, 'xxx'])  #  店铺名称这里没有爬

            print(info)
            # 存单条爬虫数据 获得主键
            try:
                datalist = [productid, timeid, platformid, storeid, info['价格'], info['手机整体评价']['好评率'],
                            info['手机整体评价']['评论数'], info['手机整体评价']['晒图'], info['手机整体评价']['追评数'],
                            info['手机整体评价']['好评数'], info['手机整体评价']['中评数'], info['手机整体评价']['差评数']]
                print('productid' ,productid)
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
                # sleeptime = random.randint(0, 9)
                # print('暂停' + str(sleeptime) + '秒')
                # logging.info('暂停' + str(sleeptime) + '秒\r')
                # time.sleep(sleeptime)
                continue

            # 下载并存图片
            # phoneImaLink = info['小图片链接']
            # for link in phoneImaLink:
            #     imgHtml = requests.get(link, stream=True, headers={
            #         'User-Agent': 'User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64) '
            #                       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari'
            #                       '/537.36 SE 2.X MetaSr 1.0'})
            #     imgHtml.encoding = imgHtml.apparent_encoding
            #
            #     SQL.insert('imgs', [pid, imgHtml.content])

            phoneImaLinkB = info['大图片链接']
            for linkB in phoneImaLinkB:
                imgHtmlB = requests.get(linkB, stream=True, headers={
                    'User-Agent': 'User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari'
                                  '/537.36 SE 2.X MetaSr 1.0'})
                imgHtmlB.encoding = imgHtmlB.apparent_encoding
                SQL.insert('imgs', [pid, imgHtmlB.content])

            # 存配置信息
            phoneProperties = info['手机配置']
            Pro = ''
            for key in phoneProperties.keys():
                Pro = Pro + '||' + key + '||' + phoneProperties[key]
            SQL.insert('raw_info', [pid, Pro])

            # 存评论
            commentsHeader = ['昵称', '用户等级', '评论星级', '内容', '机型', '发表时间', '点赞数', '评论回复次数',
                              '是否推荐', '客户端']
            userCommentList = info['手机全部评价内容']

            for comment in userCommentList:
                tempList = [pid]
                for commentInfo in commentsHeader:
                    tempList.append(comment[commentInfo])
                SQL.insert('comments', tempList)

    # 关闭SQL连接
    SQL.close()

    # 程序结束时间
    endTime = time.process_time()
    print('所有手机爬取完毕,程序耗费的时间为：', endTime - startTime)
    logging.info('所有手机爬取完毕,程序耗费的时间为：' + str(endTime - startTime) + '\r')