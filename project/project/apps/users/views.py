from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import login
import json,re
from .models import User


# 判断用户名是否重复
class UsernameCountView(View):
    def get(self,request,username):
        # 1.提取参数
        # 2. 校验参数
        # 3. 业务数据处理 - 根据用户名统计用户数量
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '数据库错误！'
            })
        # 4. 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })

# 判断手机号是否重复
class MobileCountView(View):
    def get(self,request, mobile):
    # 1. 提取参数
    # 2. 校验参数
    # 3. 业务数据处理
        count = User.objects.filter(mobile=mobile).count()
    # 4. 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'OK',
            'count': count
        })

# 用户注册接口
class RegisterView(View):
    def post(self,request):
        # 1. 提取参数
        # request.body # 请求提参数，类型为字节对象b'{"username":...}'
        data = json.loads(request.body)  # 低版本的python中，loads函数需要传入字符串，所以request.body需要deconde
        print(data)
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password')
        mobile = data.get('mobile')
        sms_code = data.get('sms_code')
        allow = data.get('allow',False)
        # 2. 校验参数
        # 2.1 必要性校验 - 必填字段
        if not all([username,password,password2,mobile,sms_code]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要参数',
            }, status=400)
        # 2.2 约束条件校验 - 长度限制
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名格式有误',
            }, status=400)
        if not re.match(r'^[a-zA-Z0-9-]{8,20}$',password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误',
            }, status=400)
        # 2此次输入是否一致
        if password != password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '两次输入密码不一致',
            }, status=400)
        # 手机号
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': '手机号格式有误',
            }, status=400)
        if not re.match(r'^\d{6}$',sms_code):
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码格式有误',
            }, status=400)
        if not isinstance(allow,bool):
            return JsonResponse({
                'code': 400,
                'errmsg': 'allow格式有误',
            }, status=400)
        # 2.3 业务性校验 - 验证码
        # TODO: 此处填充短线验证码校验逻辑代码

        # 3. 业务数据处理 - 新建User模型类对象保存数据库
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 500,
                'errmsg': '数据库写入失败'
            },status=500)

        login(request,user)

        # 4. 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'OK'
        })
