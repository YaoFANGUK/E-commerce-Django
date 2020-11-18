from django.views import View
from mall.utils.views import LoginRequiredJSONMixin
from orders.models import OrderInfo
from django.http import JsonResponse
from alipay import AliPay
from django.conf import settings
import os


class PaymentView(LoginRequiredJSONMixin, View):

    def get(self, request, order_id):
        # 1.提取参数
        user = request.user
        # 2.校验参数
        try:
            order = OrderInfo.objects.get(
                user=user,
                order_id=order_id
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'errmsg': '订单不存在'
            })

        # 3.业务数据处理 —— 通过支付宝sdk接口，获取支付页面url
        # 3.1 获取支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            # 支付成功之后，阿里服务器主动请求咱们的服务器
            # 本地服务器不具有公网ip，此处设置为None
            app_notify_url=None,
            app_private_key_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),  # payment目录
                'keys/app_private_key.pem'
            ),
            alipay_public_key_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'keys/alipay_public_key.pem'
            ),
            sign_type='RSA2',  # 默认即为RSA2加密方式
            debug=settings.ALIPAY_DEBUG
        )
        # 3.2 拼接完整的支付页面url
        # alipay_url = 支付网关 + 支付查询字符串参数
        # api_alipay_trade_page_pay:  功能： 获取网页支付url的查询字符串参数
        # alipay.api_alipay_trade_app_pay:  功能： 获取手机应用支付url
        order_string = alipay.api_alipay_trade_page_pay(
            subject='linfan商城订单： %s' % order_id,
            out_trade_no=order_id,
            total_amount=float(order.total_amount),
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=None
        )
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'alipay_url': alipay_url
        })
