from django.shortcuts import render
from django.db import DatabaseError
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.http import JsonResponse
from django.conf import settings
from oauth.models import OAuthQQUser
from mall.utils.secret import SecretOauth
from django_redis import get_redis_connection
from users.models import User
import json,re
from django.contrib.auth import login



# 1.接口1： 获取QQ扫描URL
class QQURLView(View):
    def get(self, request):
        # next 表示从哪个页面进入到的登录页面
        # 将来登录成功后，就自动回到那个页面
        # 1.提取参数
        next =  request.GET.get('next')
        # 2.校验参数
        # 3. 业务数据处理 —— 获取扫码url
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=next
        )
        login_url = oauth.get_qq_url()
        return JsonResponse({
            'code': 0,
            'errmsg': 'OK',
            'login_url':login_url
        })


class QQUserView(View):
    # 接口2： 获取openid
    def get(self,request):
        # 1.提取参数
        code = request.GET.get('code')
        # 2.校验参数
        if not code:
            # 判断 code 参数是否存在
            return JsonResponse({'code': 400,
                                      'errmsg': '缺少code参数'})
        # 3.业务数据处理 —— 获取openid
        # 调用安装的 QQLoginTool 工具类
        # 3.1.创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 3.2.携带 code 向 QQ服务器 请求 access_token
            access_token = oauth.get_access_token(code)

            # 3.3 携带 access_token 向 QQ服务器 请求 openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            # 如果上面获取 openid 出错, 则验证失败
            logger.error(e)
            # 返回结果
            return http.JsonResponse({
                'code': 400,
                'errmsg': 'oauth2.0认证失败, 即获取qq信息失败'
            })

        # 4.构建响应（绑定 / 未绑定）
        try:
            # 查看是否有 openid 对应的用户
            oauth_qq = OAuthQQUser.objects.get(openid=openid)

        except OAuthQQUser.DoesNotExist as e:
            # 如果 openid 没绑定mall用户
            auth = SecretOauth()
            access_token = auth.dumps({'openid': openid})
            return JsonResponse({
                'code': 300,
                'errmsg': 'ok',
                'access_token': access_token
            })
        else:
            # 如果 openid 已绑定商城用户
            # 根据 user 外键, 获取对应的 QQ 用户(user)
            user = oauth_qq.user

            # 实现状态保持
            login(request, user)

            # 创建重定向到主页的对象
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })

            # 将用户信息写入到 cookie 中，有效期14天
            response.set_cookie('username', user.username, max_age=3600*24*14)

            # 返回响应
            return response

    # 接口3：绑定QQ
    def post(self, request):
        """
        用户绑定到openid
        """
        # 1. 提取参数
        data = json.loads(request.body.decode())
        mobile = data.get('mobile')
        password = data.get('password')
        sms_code = data.get('sms_code')
        access_token = data.get('access_token')
        # 2. 校验参数
        # 2.1 必要性校验
        if not all([mobile, password, sms_code, access_token]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要的参数'
            })
        # 2.2 约束校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': 'mobile格式有误'
            })
        if not re.match(r'^[0-9a-zA-Z_]{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': 'password格式有误'
            })
        if not re.match(r'^\d{6}$', sms_code):
            return JsonResponse({
                'code': 400,
                'errmsg': 'sms_code格式有误'
            })
        # 2.3 业务性校验 - 短信验证码
        conn = get_redis_connection('verify_code') # 2号库
        sms_code_from_redis = conn.get('sms_%s' %mobile) # 返回验证码或者None
        if not sms_code_from_redis:
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码已过期'
            })
        if sms_code != sms_code_from_redis.decode():
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码有误'
            })

        # 3.业务数据处理 —— 绑定QQ(把用户账号和openid绑定)
        # 3.1 获取openid（解密）
        auth = SecretOauth()
        content_dict = auth.loads(access_token) # {'opendid': "asdgfbdsjh23"}
        if content_dict is None:
            # 解密失败
            return JsonResponse({
                'code': 400,
                'errmsg': 'access_token无效！'
            })
        openid = content_dict.get('openid')
        # 3.2 根据手机号查找用户
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist as e:
            # 根据手机号找不到用户 —— 用户未注册账号
            user = User.objects.create_user(
                username=mobile,
                mobile=mobile,
                password=password
            )
        else:
            # 根据手机号找到用户 —— 用户已注册账号
            # 验证用户密码
            if not user.check_password(password):
                return JsonResponse({
                    'code':400,
                    'errmsg': '密码有误'
                })

        # 将用户绑定openid
        try:
            OAuthQQUser.objects.create(
                user=user,  # 当前已注册的mall账号
                openid=openid  # 对应的qq身份
            )
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '往数据库添加数据出错'
            })

        # 4. 构建响应
        login(request, user)
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.set_cookie('username', user.username, max_age=14*3600*24)
        return response


