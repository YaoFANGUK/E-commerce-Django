from django.views import View
from mall.utils.views import LoginRequiredJSONMixin
from orders.models import OrderInfo
from .models import Payment
from django.http import JsonResponse
from alipay import AliPay
from django.conf import settings
import os


class PaymentView(LoginRequiredJSONMixin, View):
    """
    支付接口1： 获取支付页面
    """

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


class PaymentStatusView(LoginRequiredJSONMixin, View):
    """
    支付接口2： 支付成功，验证数据，保存支付流水号和修改订支付状态
    """

    def put(self, request):
        # 1.提取参数
        user = request.user
        # 提取支付宝参数
        query_dict = request.GET  # QueryDict类型
        data = query_dict.dict()  # 把QueryDict转化为dict普通字典
        # 提取签名 —— 后续根据该签名来验证数据的真伪
        # 我们需要把签名从字典中取出，并从原字典中删除： 因为后续验证的数据支付宝接口约定，需要去除签名信息
        sign = data.pop('sign')
        # 2.校验参数
        # 使用支付宝sdk，根据sign来验证data是否伪造
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            # 支付成功之后，阿里服务器主动请求服务器
            # 本地服务器不具有公网ip，此处设置为None
            app_notify_url=None,
            app_private_key_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'keys/app_private_key.pem'
            ),
            alipay_public_key_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'keys/alipay_public_key.pem'
            ),
            sign_type='RSA2',
            debug=settings.DEBUG
        )
        if not alipay.verify(data, sign):
            # 支付数据有误 —— 有可能用户伪造
            return JsonResponse({
                'code': 400,
                'errmsg': '支付失败'
            })
        # 3.业务数据处理 —— 保存支付流水号和修改订单状态
        order_id = data.get('out_trade_no')  # 订单号
        trade_no = data.get('trade_no')  # 支付流水号
        # 修改订单状态
        order = OrderInfo.objects.get(order_id=order_id)
        order.status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        order.save()
        # 保存支付流水号
        try:
            Payment.objects.create(
                order=order,
                trade_id=trade_no
            )
        except DatabaseError:
            return JsonResponse({
                'code': 500,
                'errmsg': '数据库错误'
            })
        # 4、构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'trade_id': trade_no
        })
