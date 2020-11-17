from django.shortcuts import render
from django.views import View
from goods.models import SKU
from mall.utils.cookiesecret import CookieSecret
import json
from django.http import JsonResponse
from django_redis import get_redis_connection


class CartsView(View):
    # 添加购物车
    def post(self, request):
        # 1.提取参数
        user = request.user  # 登陆用户 或 匿名用户
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')  # 1
        count = data.get('count')
        selected = data.get('selected', True)
        # 2.校验参数
        if not all([sku_id, count]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少参数'
            })
        # 3.业务数据处理 —— 记录用户登录或未登录购物车数据
        if user.is_authenticated:
            # 3.1 用户已登陆
            conn = get_redis_connection('carts')  # 5号库
            # (1) 提取原有redis购物车数据
            # redis_carts = {b'1': b'5', b'2', b'10'}
            redis_carts = conn.hgetall('carts_%s' % user.id)
            # redis_selected = [b'1', b'2']
            redis_selected = conn.smembers('selected_%s' % user.id)
            # (2)构建最新的购物车数据 —— 存在则count累加， 选中状态以最新为准
            # (3)把新的购物车数据写入redis
            if str(sku_id).encode() in redis_carts:
                # 当前sku_id商品在redis购物车中
                count = count + int(redis_carts[str(sku_id).encode()])
                conn.hset('carts_%s' % user.id, sku_id, count)
            else:
                conn.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                # 被选中， 需要把sku_id加入集合中
                conn.sadd('selected_%s' % user.id, sku_id)
            else:
                # 被取消选中，需要把sku_id从集合中移除
                conn.srem('selected_%s' % user.id, sku_id)
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
        else:
            # 3.2 用户未登录 —— 存储cookie购物车
            # (1)提取原有cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 原有cookie购物车数据存在， 解码
                cart_dict = CookieSecret.loads('carts')
            else:
                cart_dict = {}
            # (2) 构建最新的购物车数据 —— 判断要加入购物车的商品是否已经在购物车中，如有相同的商品，累加求和，反之，直接赋值
            if sku_id in cart_dict:
                # 如果当前sku_id商品在原有购物车中， 则count累加； 选中状态selected以最新的为准
                cart_dict[sku_id]['count'] += count
                cart_dict[sku_id]['selected'] = selected
            else:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            # (3) 把最新的购物车字典数据写入cookie中
            cart_str = CookieSecret.dumps(cart_dict)
            # 4. 构建响应
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
            response.set_cookie('carts', cart_str, max_age=24 * 30 * 3600)
            return response

    # 展示购物车
    def get(self, request):
        # 1.提取参数
        user = request.user
        # 2.校验参数
        # 3.业务数据处理 —— 读取购物车数据，在从mysql读取详细信息
        cart_dict = {}  # 准备一个空字典来保存购物车数据
        if user.is_authenticated:
            # 登陆
            conn = get_redis_connection('carts')
            redis_carts = conn.hgetall('carts_%s' % user.id)
            redis_selected = conn.smembers('selected_%s' % user.id)
            for k, v in redis_carts.items():
                sku_id = int(k)
                count = int(v)
                cart_dict[sku_id] = {
                    "count": count,
                    "selected": k in redis_selected
                }
        else:
            # 未登录 —— 从cookie中读取购物车字典数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = CookieSecret.loads(cart_str)
        # 构建响应
        cart_skus = []
        sku_ids = cart_dict.keys()
        for sku_id in sku_ids:
            sku = SKU.objects.get(pk=sku_id)
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'count': cart_dict[sku_id]['count'],
                'selected': cart_dict[sku_id]['selected']
            })
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'cart_skus': cart_skus
        })


