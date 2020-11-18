"""
针对购物车模块，实现额外的功能
"""
from django_redis import get_redis_connection
from mall.utils.cookiesecret import CookieSecret


def merge_cart_cookie_to_redis(request, response):
    """
    功能： 把cookie中的购物车数据合并到redis中
    :param request: 请求对象 --> 为了获取用户对象，获取cookie购物车字典数据
    :param response: 响应对象 --> 为了合并之后删除cookie购物车数据
    :return: 返回响应对象
    """
    # (1)获取用户
    user = request.user
    # (2)获取cookie购物车字典数据
    cart_str = request.COOKIES.get('carts')
    if cart_str:
        cart_dict = CookieSecret.loads(cart_str)
    else:
        cart_dict = {}
    # (3)把cookie数据合并到redis中
    conn = get_redis_connection('carts')
    redis_cart = conn.hgetall('carts_%s' % user.id)
    # 合并购物车操作流程：
    sku_ids = cart_dict.keys()
    for sku_id in sku_ids:
        # cookie选中，加入集合
        conn.hset('carts_%s' % user.id, sku_id, cart_dict[sku_id]['count'])
        if cart_dict[sku_id]['selected']:
            # cookie选中， 则加入集合
            conn.sadd('selected_%s' % user.id, sku_id)
        else:
            # cookie没选中，则从集合中除去
            conn.srem('selected_%s' % user.id, sku_id)
    # (4)删除cookie购物车数据返回响应对象
    response.delete_cookie('carts')
    return response
