from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from users.models import User
from  django_redis import get_redis_connection
import json,re

class UsernameCountView(View):
    """判断用户名是否重复注册"""
    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '访问数据库失败'
            },status=400)
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })

class MobileCountView(View):
    """判断手机号是否重复注册"""
    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '访问数据库失败'
            },status=400)
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })

class RegisterView(View):
    """用户注册业务逻辑"""
    def post(self, request):
        '''接收参数， 保存到数据库'''
        # 1. 接收参数： 请求体中的JSON数据 request.body
        json_bytes = request.body # 从请求体中获取原始的JSON数据， bytes类型
        json_str = json_bytes.decode() # 将字节流转换为字符串
        json_dict = json.loads(json_str) # 将JSON字符串转换为python标准字典

        # 2. 提取参数
        username = json_dict.get('username')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        mobile = json_dict.get('mobile')
        allow = json_dict.get('allow')
        sms_code = json_dict.get('sms_code')

        # 3. 参数校验
        # 3.1 必要性校验
        if not all([username,password,password2,mobile,sms_code]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要的参数'
            },status=400)

        # 3.2 约束条件校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名格式有误'
            }, status=400)

        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            }, status=400)

        if password != password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '两次输入的密码不一致'
            }, status=400)

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': '手机号格式有误'
            }, status=400)

        if allow != True:
            return JsonResponse({
                'code': 400,
                'errmsg': '用户未同意注册协议'
            }, status=400)

        # 3.3 业务性校验
        # 保存注册数据之前，对比短信验证码
        # 判断短信验证码是否正确：与图形验证码一样的业务逻辑
        #   提取服务端存储的短信验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        # 判断短信验证码是否过期
        if not sms_code_server:
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码失效'
            },status=400)
        # 对比用户输入的和服务器存储的短信验证码是否一致
        if sms_code != sms_code_server.decode():
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码有误'
            },status=400)

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'errmsg': '注册失败'
            }, status=500)

        # 状态保持 —— 使用session机制，把用户数据写入redis
        login(request, user)

        # 4. 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': '注册成功'
        })
