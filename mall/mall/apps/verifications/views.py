from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse,JsonResponse
from verifications.libs.captcha.captcha import captcha

class ImageCodeView(View):
    """
    图形验证码
    """
    def get(self, request, uuid):
        """
        实现图形验证码逻辑
        :param uuid UUID
        :return image.jpg
        """
        # 生成图形验证码
        text, image = captcha.generate_captcha()
        # 保存图形验证码
        # 使用配置的redis数据库别名，创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')
        # 使用连接到redis的对象去操作数据存储到redis
        # 图形验证码必须要有有效期
        redis_conn.setex('img_%s'%uuid, 300, text)
        # 响应图形验证码
        return HttpResponse(image, content_type='image/jpg')

