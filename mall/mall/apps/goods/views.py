from django.views import View
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from goods.models import GoodsCategory
from .utils import get_breadcrumb, get_goods_and_spec
from content.utils import get_categories
from .models import SKU


class ListView(View):
    """
    商品列表页
    """
    def get(self, request, category_id):
        """
        提供商品列表页
        """
        # 1. 获取参数
        page_num = request.GET.get('page')
        page_size = request.GET.get('page_size')
        sort = request.GET.get('ordering')
        # 2.校验参数
        # 判断category_id是否正确
        try:
            # 获取三级菜单分类
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'errmsg': '获取数据库数据出错'
            })

        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category_id=category_id)

        # 排序方式
        try:
            skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort)
        except SKU.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'errmsg': '获取数据库数据出错'
            })

        paginator = Paginator(skus, 5)
        # 获取每页商品数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            # 如果page_num不正确，默认返回400
            return JsonResponse({
                'code': 400,
                'errmsg': 'page数据出错'
            })

        # 获取列表页总页数
        total_page = paginator.num_pages

        # 定义列表：
        data_list = []
        # 整理格式
        for sku in page_skus:
            data_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        # 把数据转为json发送给前端
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': data_list,
            'count': total_page
        })

