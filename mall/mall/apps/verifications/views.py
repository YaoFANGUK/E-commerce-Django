from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse,JsonResponse
from verifications.libs.captcha.captcha import captcha
from verifications.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code # 使用celery异步发送短信
from mall.utils.secret import SecretOauth
import logging, random
logger = logging.getLogger('django')


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

class SMSCodeView(View):
    """
    短信验证码
    """
    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return JSON
        """
        # 1. 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        # 2.校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要参数'
            },status=400)
        # 3.创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')
        # 从redis数据库获取存入的数据
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 判断该数据是否存在，如果存在意味着用户发送短信间隔不超过60s，直接返回
        if send_flag:
            return JsonResponse({
                'code': 400,
                'errmsg': '发送短信过于频繁'
            },status=400)

        # 4. 提取图形验证码
        image_code_server = redis_conn.get('img_%s'%uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({
                'code': 400,
                'errmsg': '图形验证码失效'
            },status=400)

        # 5. 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('ims_%s' %uuid)
        except Exception as e:
            logger.error(e)

        # 6. 对比图形验证码
        # bytes 转字符串
        image_code_server = image_code_server.decode()
        # 转小写后比较
        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({
                'code': 400,
                'errmsg':'输入图形验证码有误'
            },status=400)

        # 7. 生成短信验证码： 生成6位数字验证码
        sms_code = "%06d" % random.randint(0, 999999)
        logger.info(sms_code)

        # 8. 保存短信验证码
        # 短信验证码有效期，单位：300秒
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        # 往redis中存入一个数据有效期为60s避免用户频繁发送短信
        redis_conn.setex('send_flag_%s' % mobile, 60, 1)

        # 9. 发送短信验证码
        # 短信模版
        # CCP().send_template_sms(mobile,[sms_code, 5], 1)
        ccp_send_sms_code.delay(mobile, sms_code)
        print('短信验证码: ', sms_code)

        # 10. 响应结果
        return JsonResponse({
            'code': 0,
            'errmsg': '发送短信成功'
        })


class VerifyEmailView(View):
    def put(self, request):
        # 1.接收token
        token = request.GET.get('token')
        if not token:
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少token'
            })
        # 2.解密
        data_dict = SecretOauth().loads(token)
        # 3. 去数据库对比 user_id, email
        try:
            user = User.objects.get(pk=data_dict.get('user_id'), email=data_dict.get('email'))
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '参数有误'
            })
        # 5.修改激活状态
        try:
            user.email_active = True
            user.save()
        except DatabaseError:
            return JsonResponse({
                'code': 0,
                'errmsg': '激活失败'
            })
        return JsonResponse({
            'code': 0,
            'errmsg': '激活成功'
        })