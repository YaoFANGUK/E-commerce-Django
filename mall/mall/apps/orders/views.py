from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from mall.utils.views import LoginRequiredJSONMixin
from goods.models import SKU
from users.models import Address
from decimal import Decimal


class OrderSettlementView(LoginRequiredJSONMixin, View):

    def get(self, request):
        # 1.提取参数
        user = request.user
        # 2.校验参数
        # 3.业务数据处理 —— 读取购物车数据和收货地址
        # 3.1 由于当前接口只允许登陆用户访问，那么购物车数据必然合并到redis了
        conn = get_redis_connection('carts')
        redis_cart = conn.hgetall('carts_%s' % user.id)
        redis_selected = conn.smembers('selected_%s' % user.id)
        # 3.2 读取mysql商品详细信息
        sku_ids = redis_cart.keys()
        skus = []
        for sku_id in sku_ids:
            # 当且仅当该sku被选中，才获取详细信息， 构建响应数据
            if sku_id in redis_selected:
                sku = SKU.objects.get(pk=sku_id)
                skus.append({
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'count': int(redis_cart[sku]),
                    'price': sku.price
                })
        address_queryset = Address.objects.filter(user=user)
        addresses = []
        for address in address_queryset:
            addresses.append({
                'id': address.id,
                'province': address.province.name,
                'city': addresses.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'receiver': address.receiver
            })
        freight = Decimal('10.00')  # 保证精度
        # 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'context': {
                'addresses': addresses,
                'skus': skus,
                'freight': freight  # 运费
            }
        })
