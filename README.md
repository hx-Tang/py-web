# SERVER

## 概述
insight购机指南/销售指南 微信小程序
python flask 后端
URL：www.buptdachuang2019.top/

note：项目结束，后端暂停服务

## 目录结构

```
|-- py-web                          # 后端
    |-- auth.py                     # 登陆校验
    |-- api                         # 接口实现
        |-- search.py               # 搜索
        |-- content.py              # 详情页信息
        |-- brand.py                # 品牌打分
        |-- content.py              # 详情
        |-- img.py                  # 图片
        |-- list                    # 列表信息
            |-- platforms.py        # 各平台排行
            |-- hot.py              # 热门排行 
            |-- like.py             # 兴趣排行
    |-- reptile                     # 爬虫
        |-- SQL.py                  # 数据库操作
        |-- JD.py                   # JD爬虫
        |-- TB.py                   # TB爬虫
        |-- preproc.py              # 预处理
        |-- eval.py                 # 分析
        |-- config,py               # 数据库配置
    |-- config.py                   # flask 框架配置
    |-- index.py                    # 服务入口/接口路由
    |-- README.md                   # README
```

## API
调用api时输入的数据放在URL后面的argument里  
返回值为json格式  data为元素是字典的列表  字典的keyword列在每个api下面

- `/auth`: 登陆校验 返回session id    # 暂时废弃
    * 输入： wx.login()方法返回的code
    * 返回： session_id  
    [登陆校验过程具体见链接](https://www.jianshu.com/p/c5f6c98b2685)  
    其他的api输入都要带上session_id用于维持登陆态  
    
- `/api/get_img`：根据图片号获取图片
    * 输入：req.arg: imgid
    * 返回：html：Content-Type = 'image/png'、body为图片文件    
    
- `/api/search`：根据页码 搜索商品列表
    * 输入：req.arg: page
    * 返回：json（'code': , 'message': , 'data': []）  
    data: [imgid, productid, platform, name, price, num]  
    图片号，商品id，平台，名称，价格，销量  
    
- `/api/content`：根据商品id 获取具体信息
    * 输入：req.arg: productid
    * 返回：json('code': , 'message': , 'data': [])   
    data: [imgid, platform, link, name,num，num_trend, price, price_trend，info{}, score, socre_detail{}, 
    exp_pop, keyword, comm_eval, goodcomm, badcomm, comm_imgid]  
    全部图片id[]，平台，商品链接，名称，销量，销量曲线图片id，价格，价格曲线图片id，商品参数字典{}, 产品总分，参数分值字典{}，
    兴趣指数，关键字, 好评度，典型好评评论[]， 典型差评评论[]，评论词云图
    
- `/api/list/platforms`：根据平台名/排序方式/页码 获取商品列表
    * 输入：req.arg: platformid sort page
    排序方式sort取值含义：1.价格升序 2.价格降序 3.销量升序 4.销量降序 5.综合排序
    * 返回：json('code': , 'message': , 'data': [])
    data: [imgid, productid, name, price, num] 
    图片id， 商品id， 名称，价格，销量   
    
- `/api/list/hot`：获取热销排行列表
    * 输入：req.arg: page
    * 返回：json（'code': , 'message': , 'data': []）  
    data: [imgid, productid, platform, name, price, num]  
    图片号，商品id，平台，名称，价格，销量  
    
- `/api/list/like`：获取兴趣集合列表
    * 输入：req.arg: page
    * 返回：json（'code': , 'message': , 'data': []）  
    data: [imgid, productid, platform, name, price, num]  
    图片号，商品id，平台，名称，价格，销量  
    
## 启动
```
$ cd py-web
$ python3 index.py
```
打开浏览器访问 `http://localhost:5000`。
