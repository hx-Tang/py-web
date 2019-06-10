from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_login import LoginManager, logout_user, login_user, login_required

from auth import auth as au

import api
from api.list import hot, platforms, likes
from api import search, content, NN, img, brand

from reptile import dingshi

import config
import _thread

app = Flask(__name__)
# 加载配置文件
app.config.from_object(config)
CORS(app, supports_credentials=True)

# 登录模块
login_manager = LoginManager()
# 配置用户认证信息
login_manager.init_app(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth'
login_manager.login_message = u"请重新登陆！"
login_manager.login_message_category = "info"

# 各api的路由
'''
首页：测试页面
'''



@app.route('/')
def index():
    return 'WelCome to Index Page!'


@app.route('/testSearch')
def testSearch():
    page = request.args.get('page', 1)
    result = api.search.searchAll(page)
    return jsonify({'code': '0000', 'message': '测试成功', 'data': result})

@app.route('/test')
def test():
    # result = search.searchAll(1)
    # return jsonify({'code': '0000', 'message': '测试成功', 'data': result})
    return 'WelCome to Test Page!'


'''
登陆校验: 返回session id
'''


@app.route('/auth')
def auth():
    # 读取上传的用户信息
    code = request.args.get('code', '')

    encryptedData = request.args.get('encryptedData', '')
    rawData = request.args.get('rawData', '')
    signature = request.args.get('signature', '')
    iv = request.args.get('iv', '')

    if code != '':
        # 微信登陆，获取session_id
        session_id, user = au.auth(code, encryptedData, rawData, signature, iv)
        if session_id != '':
            # 登陆
            login_user(user, True)
            # 返回sessionid给客户端保存
            return jsonify({'code': '0000', 'message': '登陆成功', 'session_id': session_id})
    return jsonify({'code': '9999', 'message': '登陆失败请重试'})


'''
退出登陆
'''


@app.route('/logout')
def logout():
    logout_user()
    return jsonify({'code': '0000', 'message': '退出登陆成功'})


'''
根据关键字搜索商品列表 需要登陆
'''


@app.route('/api/search')
# @login_required
def do_search():
    productid = request.args.get('productid', '')
    if productid != '':
        result = search.searchbyid(productid)
        return jsonify({'code': '0000', 'message': '搜索该id成功', 'data': result})
    # 查询并返回结果
    keyword = request.args.get('keyword', '')
    print(keyword)
    page = request.args.get('page', 1)
    if keyword == '':
        result = search.searchAll(page)
        return jsonify({'code': '0000', 'message': '搜索成功', 'data': result})
    result = search.search(keyword, page)
    return jsonify({'code': '0000', 'message': '搜索成功', 'data': result})


'''
根据商品id 获取具体信息 需要登陆
'''


@app.route('/api/content')
# @login_required
def do_content():
    # 查询并返回结果
    productid = request.args.get('productid', '')
    result = content.content(productid)
    if result == '':
        return jsonify({'code': '9999', 'message': '查询失败稍后重试'})
    return jsonify({'code': '0000', 'message': '成功', 'data': result})


'''
根据平台名/排序方式/页码 获取商品列表
'''


@app.route('/api/list/platforms')
def platformlist():
    # 查询并返回结果
    platformid = request.args.get('platformid', '')
    sort = request.args.get('sort', 1)
    t = request.args.get('type', '')
    page = request.args.get('page', 1)
    result = platforms.platforms(platformid, sort, page, t)
    if result == '':
        return jsonify({'code': '9999', 'message': '查询失败稍后重试'})
    return jsonify({'code': '0000', 'message': '成功', 'data': result})


'''
获取综合排行列表
'''


@app.route('/api/list/hot')
def do_hot():
    # 查询并返回结果
    page = request.args.get('page', 1)
    t = request.args.get('type', '')
    result = hot.hot(page, t)
    if result == '':
        return jsonify({'code': '9999', 'message': '查询失败稍后重试'})
    return jsonify({'code': '0000', 'message': '成功', 'data': result})


'''
根据热门型号名获取商品列表
'''

#
# @app.route('/api/list/hot/sublist')
# def hotsublist():
#     # 查询并返回结果
#     hotid = request.args.get('hotid', '')
#     result = hotsublist.hotsublist(hotid)
#     if result == '':
#         return jsonify({'code': '9999', 'message': '查询失败稍后重试'})
#     return jsonify({'code': '0000', 'message': '成功', 'data': result})


'''
根据热门型号名获取分析报告 需要登陆
'''

#
# @app.route('/api/list/hot/content')
# @login_required
# def hotcontent():
#     # 查询并返回结果
#     hotid = request.args.get('hotid', '')
#     result = hotcontent.hotcontent(hotid)
#     if result == '':
#         return jsonify({'code': '9999', 'message': '查询失败稍后重试'})
#     return jsonify({'code': '0000', 'message': '成功', 'data': result})


'''
根据页码获取受欢迎度排行列表
'''
@app.route('/api/list/likes')
def do_likes():
    # 查询并返回结果
    page = request.args.get('page', 1)
    result = likes.likes(page)
    if result == '':
        return jsonify({'code': '9999', 'message': '查询失败稍后重试'})
    return jsonify({'code': '0000', 'message': '成功', 'data': result})

''''
获取图片
'''
@app.route('/api/img')
def getimg():
    # 查询并返回结果

    imgid = request.args.get('imgid', '')
    response = img.get_img(imgid)

    return response

@app.route('/api/comm_img')
def getcomm_img():
    # 查询并返回结果

    imgid = request.args.get('imgid', '')
    response = img.get_comm_img(imgid)

    return response

@app.route('/api/test_img')
def gettest_img():
    # 查询并返回结果

    response = img.get_img(20)

    return response

@app.route('/api/NN')
def doNN():
    phone = {}
    phone['brand'] = request.args.get('brand', '小米')
    phone['fpixel'] = float(request.args.get('fpixel', 1200))
    phone['bpixel'] = float(request.args.get('bpixel', 800))
    phone['cpu'] = float(request.args.get('cpu', 5))
    phone['screen'] = float(request.args.get('screen', 6))
    phone['sim'] = float(request.args.get('sim', 2))
    phone['thick'] = float(request.args.get('thick', 7))
    phone['weight'] = float(request.args.get('weight', 200))
    phone['price'] = float(request.args.get('price', 3))

    result = NN.nn(phone)

    if result == '':
        return jsonify({'code': '9999', 'message': '查询失败!'})

    return jsonify({'code': '0000', 'message': '成功', 'data': result})

@app.route('/api/brandscore')
def getbrandscore():
    p = request.args.get('price', '')

    result = brand.brandscore(p)

    if result == '':
        return jsonify({'code': '9999', 'message': '查询失败!'})

    return jsonify({'code': '0000', 'message': '成功', 'data': result})



if __name__ == "__main__":
    app.run()


