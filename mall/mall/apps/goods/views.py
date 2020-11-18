from django.views import View
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from goods.models import GoodsCategory
from .utils import get_breadcrumb, get_goods_and_spec
from content.utils import get_categories
from .models import SKU
from django.db import DatabaseError
from haystack.views import SearchView


class ListView(View):
    """
    商品列表页
    """

    def get(self, request, category_id):
        """
        提供商品列表页
        """
        # 1. 获取参数
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')
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

        # 3.业务数据处理 —— 根据分类过滤sku商品，排序分页返回
        # 3.1 过滤加排序
        try:
            skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by(ordering)
        except SKU.DoesNotExist:
            return JsonResponse({
                'code': 400,
                'errmsg': '获取数据库数据出错'
            })
        # 3.2 分页
        # (1)获取分页器对象
        paginator = Paginator(skus, page_size)
        # page_skus 也是一个查询集，是分页之后取得的当前页数据查询集
        try:
            # (2) 获取每页商品数据, 找对象的方法获取所需的页数据
            page_skus = paginator.page(page)
        except EmptyPage:
            # 如果page_num不正确，默认返回400
            return JsonResponse({
                'code': 400,
                'errmsg': '页面不存在'
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


class HotGoodsView(View):
    """
    商品热销排行
    根据路径参数 category_id 查询出该类商品销量前二的商品
    """

    def get(self, request, category_id):
        """
        提供商品热销排行 JSON 数据
        """
        # 根据销量排序
        try:
            skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]  # 销量前二
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '获取商品出错'
            })

        # 转换格式
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'OK',
            'hot_skus': hot_skus
        })


class MySearchView(SearchView):
    """
    重写SearchView类, 搜索SKU商品
    该视图中默认已经提供了一个get方法响应GET请求，并且已经实现了根据参数检索数据
    """

    def create_response(self):
        # 1.获取ES搜索的结果
        context = self.get_context()
        # object_list是一个列表，保存了Haystack查询的结果Result对象
        results = context['page'].object_list
        data_list = []
        for result in results:
            sku = result.object
            data_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url,
                # 用户搜索的关键词
                'searchkey': context.get('query'),
                # 页面总数
                'page_size': context['page'].paginator.num_pages,
                # 查询的总数量
                'count': context['page'].paginator.count
            })
        return JsonResponse(data_list, safe=False)
