from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from mall.utils.views import LoginRequiredJSONMixin
from goods.models import SKU
from users.models import Address
from decimal import Decimal
import json
from django.utils import timezone
from django.db import transaction
from goods.models import SKU


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
                    'count': int(redis_cart[sku_id]),
                    'price': sku.price
                })
        address_queryset = Address.objects.filter(user=user)
        addresses = []
        for address in address_queryset:
            addresses.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.district.name,
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


class OrderCommitView(LoginRequiredJSONMixin, View):
    """
    提交订单 —— 新建订单和订单商品数据保存数据库
    """

    def post(self, request):
        # 1.提取参数
        user = request.user
        data = json.loads(request.body.decode())
        address_id = data.get('address_id')
        pay_method = data.get('pay_method')

        # 提取购物车商品数据
        conn = get_redis_connection('carts')
        redis_carts = conn.hgetall('carts_%s' % user.id)
        redis_selected = conn.smembers('selected_%s' % user.id)
        cart_dict = {}
        for k, v in redis_carts.items():
            if k in redis_selected:
                sku_id = int(k)
                count = int(v)
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': True
                }
        # 2.校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少参数'
            })
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'errmsg': '地址不存在'
            })
        if not pay_method in [OrderInfo.PAY_METHOD_ENUM['CASH'], OrderInfo.PAY_METHOD_ENUM['ALIPAY']]:
            return JsonResponse({
                'code': 400,
                'errmsg': '支付方式不支持'
            })
        # 3.业务数据处理 —— 新建订单和订单商品数据保存数据库
        # 3.1 新建订单表数据 OrderInfo
        # datetime.now() = datetime.datetime(2020, 11, 18, 15, 10, 27, 812047)  缺少了时区
        # 我们在Django工程中获取时间所属时区应该以 TIME_ZONE = 'Asia/Shanghai'为准
        # 解决: timezone.localtime()  --> 获取本地时间(指的是TIME_ZONE指定的时区的本地当前时间)
        cur_time = timezone.localtime()  # 返回值是一个时间点对象
        # cur_time.strftime('%Y%m%d%H%M%S')  -->  '20201118151742'
        # order_id = '20201118151742' + '000011'
        order_id = cur_time.strftime('%Y%m%d%H%M%S') + "%06d" % user.id
        with transaction.atomic():
            # 在订单新建之前，设置一个保存点，用于回滚
            save_id = transaction.savepoint()
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=total_count,  # 初始化为0， 后续再统计
                total_amount=total_amount,  # 初始化为0， 后续再统计
                freight=Decimal('10.00'),
                pay_method=pay_method,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            )
            # 3.2 新建订单商品表数据OrderGoods
            sku_ids = cart_dict.keys()  # [1,2] 购物车中选中的商品id
            for sku_id in sku_ids:
                # 每遍历出一个sku_id，就需要往OrderGoods表中插入一条数据
                sku = SKU.objects.get(pk=sku_id)
                # 获取旧库存和销量
                old_stock = sku.stock
                old_sales = sku.sales
                # 判断库存够不够，修改销量和库存
                count = cart_dict[sku_id]['count']  # 用户当前sku商品的下单数量
                if count > old_stock:
                    # 回滚到事务一开始的保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({
                        'code': 400,
                        'errmsg': '库存不足'
                    })
                # 修改SKU库存和数量
                sku.stock -= count
                sku.sales += count
                sku.save()
                # 修改SPU销量
                sku.spu.sales += count
                sku.spu.save()
                # 统计订单中的商品总数和订单总价格
                order.total_count += count
                order.total_amount += sku.price * count
                # 新建订单商品数据，关联sku和订单
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,  # 下单数量
                    price=sku.price
                )

            order.total_amount += Decimal('10.00')
            order.save()
            # 清除保存点
            transaction.savepoint_commit(save_id)

        # 3.3 删除购物车中选中的sku商品(买过的商品)
        sku_ids = cart_dict.keys()
        p = conn.pipeline()
        p.hdel('carts_%s' % user.id, *sku_ids)
        p.srem('selected_%s' % user.id, *sku_ids)
        p.execute()

        # 4.构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'order_id': order_id
        })
