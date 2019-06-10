from flask import request, current_app, jsonify
import requests, json
from flask_login import login_user
from auth.config import grant_type, appid, secret
from reptile.SQL import User, SQL

import base64
import json
# from Crypto.Cipher import AES

def auth(code,encryptedData,rawData,signature,iv):
    # TODO 解码用户信息
    db = SQL('webdb')
    # 用js_code，appid，secret，grant_type向微信服务器获取session_key,openid,expires_in
    data = {}
    data['appid'] = appid
    data['secret'] = secret
    data['js_code'] = code
    data['grant_type'] = grant_type
    res = requests.get('https://api.weixin.qq.com/sns/jscode2session', params=data).json()

    if res.has_key('session_key'):
        session_key = res['session_key']
        expires_in = res['expires_in']
        openid = res['openid']

        # 根据openid是否插入用户
        user = User.query.filter_by(openId=openid).first()
        if user is None:
            loginkey = base64.b64decode(openid)
            rData = json.loads(rawData)
            user = User(openId=openid,
                        loginkey=loginkey,
                        nickName=rData['nickName'],
                        gender=rData['gender'],
                        city=rData['city'],
                        province=rData['province'],
                        country=rData['country'],
                        avatarUrl=rData['avatarUrl'],
                        cashbox=0)
            db.session.add(user)
            db.session.commit()
            db.close()
            return loginkey, user
    db.close()
    return '', ''


# 验签数据
import hashlib
def sha1Sign(session_key, rawData):
  data = '%s%s' % (rawData.encode('utf8'), session_key)
  return hashlib.sha1(str(data)).hexdigest()


# # 解密加密数据，获取watermark中的appid
# def decrypt(session_key, encryptedData, iv):
#   sessionKey = base64.b64decode(session_key)
#   encryptedData = base64.b64decode(encryptedData)
#   iv = base64.b64decode(iv)
#
#   cipher = AES.new(sessionKey, AES.MODE_CBC, iv)
#   s = cipher.decrypt(encryptedData)
#   decrypted = json.loads(s[:-ord(s[len(s)-1:])])
#   return decrypted['watermark']['appid']