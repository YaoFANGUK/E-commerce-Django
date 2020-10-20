from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.http import JsonResponse, HttpResponse
import re, random
# get_redis_connection


# 获取验证码接口
class ImageCodeView(View):
    def get(self,request, uuid):
        # 1. 提取参数
        text, image = captcha.generate_captcha()
        # 2. 校验参数
        # 3. 业务数据处理
        try:
            conn = get_redis_connection('verify_code') # 2号库
            conn.set("img_%s"%uuid, text)
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': 'redis写入图形验证码失败',
            },status=500)
        # 4. 构建响应
        return HttpResponse(image, content_type='image/jpeg')

# 发送短信验证码接口
class SMSCodeView(View):
    def get(self, request, mobile):
        # 1. 提取参数
        image_code = data = request.GET.get('image_code') # 用户填写的图片验证码
        uuid = request.GET.get('image_code_id') # 用户图形验证码的uuid
        # 2. 校验参数
        if not all([image_code,uuid]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要参数'
            })
        if not re.match(r'^[a-zA-Z0-9]{4}$',image_code):
            return JsonResponse({
                'code': 400,
                'errmsg': '图形验证码格式有误'
            })
        if not re.match(r'^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$', uuid):
            return JsonResponse({
                'code': 400,
                'errmsg': 'uuid格式有误'
            })
        # 图形验证码校验 - 根据uuid获取redis中的图形验证码，和用户填写的比对
        conn = get_redis_connection('verify_code') # 2号库
        text = conn.get('img%s'%uuid)  # redis客户端读取返回的数据统一为字节类型 e.g., b"TYUP"
        # 如果图形验证码expire, text为None
        if not text:
            return JsonResponse({
                'code': 400,
                'errmsg': '图形验证码过期'
            })
        elif image_code.lower() != text.decode().lower(): # 统一转化为小写
            return JsonResponse({
                'code': 400,
                'errmsg': '图形验证码输入错误!'
            })
        # 3. 业务数据处理
        # 生成固定6位数的0-9组成的验证码
        sms_code = "%06d"%random.randrange(0,999999)
        print('短信', sms_code)
        # 把短信验证码写入redis
        conn.setex('sms_%s'%mobile, 300, sms_code)
        ccp = CCP()
        ccp.send_template_sms(
            mobile,
            ['sms_code', 5],
            1
        )
        # 4. 构建响应