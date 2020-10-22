### 1. 工程目录
- `statics`:前端静态文件
- `project`: 项目文件
    - `project`: 项目
        - `apps`: 专门管理子应用的包
            - users: 用户登陆应用
            - verification: 验证子应用
            - libs:
                - captcha: 第三方图形验证码生成SDK
                - yuntongxun: 第三方短信验证码SDK 
        -  `logs`: 用于存放日志文件
        - `settings`: 设置文件
            - `dev.py`: 开发时使用的配置文件
            - `prod.py`: 项目上线使用的配置文件
        - `templates`: 存放模板
        -  `utils`: 工具目录
 
 