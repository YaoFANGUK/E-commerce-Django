from django.shortcuts import render
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.http import JsonResponse
from django.conf import settings
from oauth.models import OAuthQQUser
from mall.utils.secret import SecretOauth



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

# 接口2： 获取openid
class QQUserView(View):

    def get(self,request):
        # 1.提取参数
        code = request.GET.get('code')
        # 2.校验参数
        if not code:
            # 判断 code 参数是否存在
            return http.JsonResponse({'code': 400,
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