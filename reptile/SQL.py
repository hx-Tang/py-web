# SQL操作类，定义各表并封装数据操作方法
import datetime
from _pydecimal import Decimal

import sqlalchemy
import logging

from flask_login import UserMixin, login_manager
from sqlalchemy import create_engine, BigInteger, Numeric, DateTime, Float
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import Column, String, Integer, LargeBinary, Text, Date, BLOB, Boolean, Float
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.elements import or_, and_
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for
import config
# from config import host, user, password

host = '39.96.24.26:3306'
user = 'thx'
password = 'thx'

Base = declarative_base()       # 数据表基类
Web_Base = declarative_base()   # web应用数据表的基类

class SQL:
    # 初始化连接
    def __init__(self, db_name):
        # 数据库名
        self.db_name = db_name
        # 获取时间
        self.time = datetime.datetime.now().strftime('%Y_%m_%d')

        # 连接数据库
        self.engine = create_engine(
            "mysql+pymysql://" + user + ":" + password + "@" + host + "/" + self.db_name + "?charset=utf8")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def check(self, data):
        # print(data[1])
        data[1] = self.query_id('products', [data[1]])
        # print(data[1])
        if data[1] == 0:
            return 0
        elif len(self.session.query(phones).filter(and_(phones.timeid == data[0]),
                                              phones.productid == data[1]).all()) != 0:
            return 1
        return 0

    # 重构后的简单插入方法
    def Insert(self, table=None, **kwargs):
        if not table:
            raise Exception('table is not clarified!')
        obj = table(**kwargs)
        self.session.add(obj)
        self.session.commit()

    # 数据插入方法 要求相应的data数组里按顺序放好值
    def insert(self, table, data):
        # 字典实现switch结构 组装相应table的对象
        data = data + [None, None, None, None, None, None, None, None, None, None, None]
        data_obj = {
            'times': lambda data: times(time=data[0]),
            'platforms': lambda data: platforms(platform=data[0]),
            'products': lambda data: products(product=data[0], platformid=data[1], name=data[2]),
            'stores': lambda data: stores(store=data[0], platformid=data[1], name=data[2], status=data[3]),
            'phones': lambda data: phones(productid=data[0], timeid=data[1], platformid=data[2], storeid=data[3],
                                          price=data[4], goodrate=data[5], num=data[6], pic=data[7], add=data[8],
                                          good=data[9], mid=data[10], bad=data[11]),
            'comments': lambda data: comments(pid=data[0], nickname=data[1], level=data[2], star=data[3],
                                              content=data[4], type=data[5], time=data[6], like=data[7],
                                              reply=data[8], reco=data[9], client=data[10]),
            'raw_info': lambda data: raw_info(pid=data[0], info=data[1]),
            'phone_info': lambda data: phone_info(pid=data[0], pixel=data[1], cam=data[2], cpu=data[3], screen=data[4],
                                                  sim=data[5], thick=data[6], weight=data[7]),
            'comments_eval': lambda data: comments_eval(pid=data[0], eval=data[1]),
            'imgs': lambda data: imgs(pid=data[0], img=data[1])
        }[table](data)

        # 防止重复插入
        if table == 'phones' and len(self.session.query(phones).filter(and_(phones.timeid == data[1]),
                                                                       phones.productid == data[0]).all()) != 0:
            return -1
        elif (table == 'times' or table == 'products' or table == 'stores') and self.query_id(table,
                                                                                              [data[0], data[1]]) != 0:
            print(table + '表数据已存在')
            logging.info(table + '表数据已存在\r')
            return self.query_id(table, [data[0], data[1]])
        elif table == 'comments':
            flg = 0
            for i in range(len(data)):
                if data[i] != -1:
                    flg = 1
            if flg == 0:
                return

        if data_obj == '':
            print("无效表名")
            logging.error("无效表名\r")
        else:
            try:
                self.session.add(data_obj)
                self.session.commit()
            # except sqlalchemy.exc.IntegrityError:
            #     print(table + '表数据已存在')
            #     logging.info(table + '表数据已存在\r')
            #     self.session.rollback()
            except sqlalchemy.exc.DataError as ex:
                print(table + '表数据异常' + str(ex))
                logging.info(table + '表数据异常\r' + str(ex) + '\r')
                self.session.rollback()
        return self.query_id(table, [data[0], data[1]])

    # 数据删除
    def delete(self, data):
        self.session.delete(data)
        self.session.commit()

    # 提取主键(平台，时间，产品，店铺，单条数据)
    def query_id(self, table, data):
        try:
            obj = {
                'platforms': lambda data: self.session.query(platforms).filter(platforms.platform == data[0]).one(),
                'times': lambda data: self.session.query(times).filter(times.time == data[0]).one(),
                'products': lambda data: self.session.query(products).filter(products.product == data[0]).one(),
                'stores': lambda data: self.session.query(stores).filter(stores.store == data[0]).one(),
                'phones': lambda data: self.session.query(phones).filter(and_(phones.timeid == data[1]),
                                                                         phones.productid == data[0]).one()
            }[table](data)
            return obj.id
        except:
            return 0

    # 提取原始参数
    def get_info(self, pid):
        result = self.session.query(raw_info).filter(raw_info.pid == pid).one()
        info = result.info
        return info

    # 提取评论
    def get_comment(self, pid):
        results = self.session.query(comments).filter(comments.pid == pid).all()
        commentlist = []
        if results:
            for result in results:
                commentlist.append(result.content)
        return commentlist

    # 提取历史价格
    def get_prices(self, pid):
        results = self.session.query(phones).filter(phones.id == pid).all()
        pricelist = []
        for result in results:
            time = self.session.query(times).filter(times.id == result.timeid).one().time
            pricelist.append((time, result.price))
        return pricelist

    # 提取所有时间
    def get_time(self):
        results = self.session.query(times).all()
        timedic = {}
        for result in results:
            time = self.session.query(times).filter(times.id == result.timeid).one().time
            timedic.update({result.id: time})
        return timedic, results

    # 添加表
    def init_db(self):
        Base.metadata.create_all(self.engine)

    def init_webdb(self):
        Web_Base.metadata.create_all(self.engine)

    # 删除表
    def drop_db(self):
        Base.metadata.drop_all(self.engine)

    def drop_webdb(self):
        Web_Base.metadata.drop_al(self.engine)

    # 关闭连接
    def close(self):
        self.session.close()
        self.engine.dispose()
        print('connection closed')


# 数据表:

# 时间
class times(Base):
    __tablename__ = "times"
    id = Column(Integer, primary_key=True)  # 主键
    time = Column(String(10), nullable=False, index=True, unique=True)  # 爬虫日期
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 平台
class platforms(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)  # 主键
    platform = Column(String(8), nullable=False, unique=True)  # 平台名
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 手机型号表
class models(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True)  # 主键
    model = Column(String(50), nullable=False, unique=True)  # 型号名
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

# 品牌表
class brands(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True)  # 主键
    name = Column(String(70), index=True, )  # 品牌名
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

# 商品列表
class products(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)  # 主键
    platformid = Column(Integer, ForeignKey('platforms.id'))  # 平台
    modelid = Column(Integer, ForeignKey('models.id'), nullable=True)  # 型号
    product = Column(BigInteger, index=True, unique=True)  # 商品id
    name = Column(String(70), index=True, )  # 商品名
    brandid = Column(Integer, ForeignKey('brands.id'), nullable=True)  # 品牌id
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

# 店铺表
class stores(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True)  # 主键
    platformid = Column(Integer, ForeignKey('platforms.id'))  # 平台
    store = Column(BigInteger, index=True, unique=True)  # 商家id
    name = Column(String(20), index=True)  # 商家名
    status = Column(String(20), index=True)  # 自营/第三方
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 单次爬虫手机表 包括销量及好评信息
# headers = ['名称', '价格', '好评率', '评论数', '晒图', '追评数', '好评数', '中评数', '差评数']
class phones(Base):
    __tablename__ = "phones"
    id = Column(Integer, primary_key=True)  # 主键
    platformid = Column(Integer, ForeignKey('platforms.id'))  # 平台
    timeid = Column(Integer, ForeignKey('times.id'))  # 爬虫日期
    productid = Column(Integer, ForeignKey('products.id'))  # 商品号
    storeid = Column(Integer, ForeignKey('stores.id'))  # 店铺号
    price = Column(Integer, index=True)  # 价格
    goodrate = Column(Integer)  # 好评率
    num = Column(Integer)  # 销量/评论数
    pic = Column(Integer)  # 晒图
    add = Column(Integer)  # 追评数
    good = Column(Integer)  # 好评数
    mid = Column(Integer)  # 中评数
    bad = Column(Integer)  # 差评数
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 评论表
# commentsHeader = ['昵称', '用户等级', '评论星级', '内容', '机型', '发表时间', '点赞数', '评论回复次数', '是否推荐', '客户端']
class comments(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('phones.id'))
    nickname = Column(String(20))  # 昵称
    level = Column(String(10))  # 用户等级
    star = Column(String(10))  # 评论星级
    content = Column(Text)  # 内容 **重点**
    type = Column(String(50))  # 机型
    time = Column(String(20))  # 发表时间
    like = Column(Integer)  # 点赞数
    reply = Column(Integer)  # 评论回复次数
    reco = Column(Boolean)  # 是否推荐
    client = Column(String(30))  # 客户端
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 原始配置信息
class raw_info(Base):
    __tablename__ = "raw_info"
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('phones.id'))
    info = Column(Text)  # 逗号分割的原始信息
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 分割后配置信息
class phone_info(Base):
    __tablename__ = "phone_info"
    id = Column(Integer, primary_key=True)
    productid = Column(Integer, ForeignKey('products.id'))  # 商品id
    brand = Column(String(20), index=True)  # 品牌
    fpixel = Column(Integer, index=True)  # 前摄像头像素
    bpixel = Column(Integer, index=True)  # 后摄像头像素
    cpu = Column(Integer, index=True)  # cpu
    screen = Column(Float, index=True)  # 屏幕大小
    sim = Column(Integer, index=True)  # sim数量
    thick = Column(Integer, index=True)  # 机身厚度
    weight = Column(Integer, index=True)  # 重量
    month = Column(Integer, index=True)  # 重量
    year = Column(Integer, index=True)  # 重量
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 评论倾向打分
class comments_eval(Base):
    __tablename__ = "comments_eval"
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('phones.id'))
    eval = Column(Integer)
    keywords = Column(Text)  # 逗号分割的关键字信息
    img = Column(BLOB)
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# 图片
class imgs(Base):
    __tablename__ = "imgs"
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('phones.id'))
    img = Column(BLOB)
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

# 每日分析结果
class evalresult(Base):
    __tablename__ = "evalresult"
    id = Column(Integer, primary_key=True)
    current_timeid = Column(Integer, ForeignKey('times.id'))  # 记录日期
    data_timeid = Column(Integer, ForeignKey('times.id'))  # 该商品最近一次数据的时间戳
    productid = Column(Integer, ForeignKey('products.id'))  # 商品号
    platformid = Column(Integer, ForeignKey('platforms.id'))  # 平台
    storeid = Column(Integer, ForeignKey('stores.id'))  # 店铺号
    infoid = Column(Integer, ForeignKey('raw_info.id'))  # 商品详情信息
    imgid = Column(Text)  # 商品图片
    price = Column(Integer, index=True)  # 当前价格
    price_trend = Column(Text)  # 预测价格
    goodrate = Column(Integer)  # 好评率
    num = Column(Integer)  # 销量/评论数
    num_trend = Column(Text)  # 预测销量
    score = Column(Integer)  # 基于销量情况的产品力打分
    score_detail = Column(Text)    # 打分细节 键值对
    exp_pop = Column(Integer)     # 产品受欢迎程度的神经网络预测
    comm_eval = Column(Integer)    # 好评度打分 基于评论语义分析
    goodcomm = Column(Text)     # 商品好评评论
    badcomm = Column(Text)      # 商品差评评论
    keywords = Column(Text)  # 评论关键字 逗号分割
    comm_imgid = Column(Integer, ForeignKey('comm_img.id'))  # 评论词云图
    price_num = Column(Integer)  # 价格销量曲线
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

class nnresult(Base):
    __tablename__ = "nnresult"
    id = Column(Integer, primary_key=True)
    timeid = Column(Integer, ForeignKey('times.id'))  # 记录日期
    weightdic = Column(Text)
    path = Column(Text)
    fpixelmax = Column(Float)
    bpixelmax = Column(Float)
    screenmax = Column(Float)
    thickmax = Column(Float)
    weightmax = Column(Float)
    pricemax = Column(Float)
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

class comm_img(Base):
    __tablename__ = "comm_img"
    id = Column(Integer, primary_key=True)
    img = Column(BLOB)
    __table_args__ = {
        'mysql_charset': 'utf8'
    }


# # 热门表 每天更新一次
# class hotlist(Base):
#     __tablename__ = "hotlist"
#     id = Column(Integer, primary_key=True)
#     ranking = Column(Integer, index=True)  # 排名
#     timeid = Column(Integer, ForeignKey('times.id'))  # 记录日期
#     modelid = Column(Integer, ForeignKey('models.id'))  # 型号名
#     price = Column(Integer, index=True)  # 当前价格
#     goodrate = Column(Integer)  # 当前好评率
#     num = Column(Integer, index=True)  # 当前销量
#     __table_args__ = {
#         'mysql_charset': 'utf8'
#     }

# # 优惠事件表 每天更新一次
# class events(Base):
#     __tablename__ = "events"
#     id = Column(Integer, primary_key=True)
#     timeid = Column(Integer, ForeignKey('times.id'))  # 记录日期
#     productid = Column(Integer, ForeignKey('products.id'))  # 商品号
#     message = Column(String(30))  # 优惠信息
#     price = Column(Integer, index=True)  # 当前价格
#     price_trend = Column(Integer, index=True)  # 预期价格
#     comment_rate = Column(Integer)  # 当前评价打分
#     num = Column(Integer, index=True)  # 当前销量
#     __table_args__ = {
#         'mysql_charset': 'utf8'
#     }


# web应用数据表
# 用户表
class User(UserMixin, Web_Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True)
    loginkey = Column(String(50), unique=True, nullable=False)
    openid = Column(String(50), unique=True, nullable=False)
    nickName = Column(String(100), nullable=False)
    gender = Column(Integer)
    city = Column(String(40))
    province = Column(String(40))
    country = Column(String(40))
    avatarUrl = Column(String(200))
    cashbox = Column(Numeric(8, 2), default=0.0)
    cTimestamp = Column(DateTime, index=True, default=datetime.datetime.now())

    __table_args__ = {
        'mysql_charset': 'utf8'
    }
    # # 授权token生成器
    # def generate_auth_token(self, expiration=3600):
    #     s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    #     return s

    def __repr__(self):
        return 'User %r' % self.nickName

        # 序列化转换: 资源->JSON

    def to_json(self):
        json_user = {
            'uri': url_for('api.get_user', id=self.id, _external=True),
            'openId': self.openId,
            'nickName': self.nickName,
            'gender': self.gender,
            'city': self.city,
            'province': self.province,
            'country': self.country,
            'avatarUrl': self.avatarUrl,
            'cashbox': str(self.cashbox),
            'cTimestamp': self.cTimestamp.strftime('%Y-%m-%d')
        }
        return json_user

    # 序列化转换：JSON->资源
    @staticmethod
    def from_json(json_user):
        openId = json_user.get('openId')
        nickName = json_user.get('nickName')
        gender = json_user.get('gender')
        city = json_user.get('city')
        province = json_user.get('province')
        country = json_user.get('country')
        avatarUrl = json_user.get('avatarUrl')
        cashbox = Decimal(json_user.get('cashbox'))
        #    if body is None or body = '':
        #      raise ValidationError('user does not hava a name')
        return User(openId=openId, nickName=nickName, gender=gender, city=city, province=province, country=country,
                    avatarUrl=avatarUrl, cashbox=cashbox)





# 入口
if __name__ == '__main__':
    SQL = SQL('testdb')
    # SQL = SQL('webdb')
    # SQL.drop_db()
    SQL.init_db()
    # SQL.init_webdb()
    # SQL.insert('platforms', ['JD'])
    # SQL.insert('platforms', ['TB'])
    # SQL.insert('platforms', ['GM'])
    # SQL.insert('platforms', ['SN'])
    SQL.close()

    # drop_db()
    # Base.metadata.tables['user'].create(engine, checkfirst=True)
    # pass
