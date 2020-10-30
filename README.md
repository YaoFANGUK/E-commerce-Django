#### 0. 项目说明
> 此项目为二手交易平台的Django框架后端实现，前端使用MEIDUO进行模拟，为其提供接口服务。
- 前端静态服务器：http://www.linfaner.top:8080/ (python http.server)
- 后端动态(接口)服务器: http://www.linfaner.top:8000/ (django)
- 测试账号：alyyf1 qwer1234

#### 1. 工程目录
- `statics`:前端静态文件
- `data`:
    - `data.tar.gz`: 商品图片测试数据
    - `restart_fdfs_container.sh`: docker下fdfs启动脚本
- `mall`: 项目目录
    - `celery_tasks`: 异步任务模块
    - `script`: 数据库数据恢复sql
    - `mall`: 项目
        - `apps`: 专门管理子应用的包
            - `oauth`: 第三方登录
            - `users`: 用户登陆应用
            - `verifications`: 验证子应用
                - `libs`: 工具类
                    - `captcha`: 第三方图形验证码生成SDK
                    - `yuntongxun`: 第三方短信验证码SDK 
        -  `logs`: 用于存放日志文件
        - `settings`: 设置文件
            - `dev.py`: 开发时使用的配置文件
            - `prod.py`: 项目上线使用的配置文件
        - `templates`: 存放模板
        -  `utils`: 工具目录
 
#### 2. 接口实现 
> [GET] 查找用户是否注册：
```
http://www.linfaner.top:8000/usernames/fangyao/count/
```
> [GET] 判断手机号知否已经注册过 
```
http://www.linfaner.top:8000/mobiles/13188888888/count/
```
> [POST] 用户注册接口
```
http://www.linfaner.top:8000/register/
```
> [GET] 获取图片验证码
```
http://www.linfaner.top:8000/image_codes/550e8400-e29b-41d4-a716-446655440000/
```
> [POST] 用户登陆
```
http://www.linfaner.top:8000/login/
```
> [GET] 短信验证码
```
http://www.linfaner.top:8000/sms_codes/13188888888/
```
> [PUT] 邮箱验证
```
http://www.linfaner.top:8000/emails/verification/
```
> [GET] QQ登陆 （获取QQ扫码URL）
```
http://www.linfaner.top:8000/qq/authorization/
```
> [GET/POST] QQ登陆回调 (GET获取openid，POST绑定QQ)
```
http://www.linfaner.top:8000/oauth_callback/
```
> [GET] 商品列表页
```
http://127.0.0.1:8000/list/115/skus/?page=1&page_size=5&ordering=-create_time
```

 #### 3. 效果预览
 - 邮箱验证

 <img src="https://s1.ax1x.com/2020/10/25/Bm2YtK.png" alt="" width="500">
 
 - 短信验证
 
 <img src="https://s1.ax1x.com/2020/10/25/Bm2tfO.jpg" alt="" width="250" >
 
 
 #### Reference:
 
 [FastDFS搭建](https://support.huaweicloud.com/prtg-kunpengat/fastdfs_01_0001.html)
 
 [已有nginx添加模块](https://blog.seosiwei.com/detail/28)
 
 