### 0. 项目说明
> 此项目为二手交易平台的Django框架后端实现，前端使用MEIDUO进行模拟，为其提供接口服务。
- 前端静态服务器：http://www.linfaner.top:8080/ (python http.server)
- 后端动态(接口)服务器: http://www.linfaner.top:8000/ (django)

### 1. 工程目录
- `statics`:前端静态文件
- `mall`: 项目目录
    - `mall`: 项目
        - `apps`: 专门管理子应用的包
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
 
 