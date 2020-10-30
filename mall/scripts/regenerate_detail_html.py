import sys, os
# 把外层mall加入导包路径
sys.path.insert(0,
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )

# 在一个独立的脚本中手动加载django配置文件导包路径
os.environ['DJANGO_SETTINGS_MODULE'] = 'mall.settings.dev'
# 手动加在配置文件
import django
django.setup()

from django.conf import settings
from django.template import loader
from goods.utils import get_breadcrumb, get_goods_and_spec
from content.utils import get_categories
from goods.models import SKU


# 生成静态详情页
def generate_static_sku_detail_html(sku):
    """
    功能：生成指定sku商品的静态化页面
    :param sku: sku商品对象
    :return 无
    """
    # 1. 构建模板函数
    categories = get_categories()
    breadcrumb = get_breadcrumb(sku.category.id)
    goods, sku, specs = get_goods_and_spec(sku.id)
    context = {
        'categories': categories,  # 渲染分类
        'breadcrumb': breadcrumb,  # 渲染导航
        'goods': goods,  # 商品价格等信息
        'sku': sku,
        'specs': specs,  #商品规格等信息
    }
    # 2. 渲染页面
    # 2.1 获取模板对象
    template = loader.get_template('detail.html')
    # 2.2 传入模板参数，渲染页面得到完整的页面数据
    html = template.render(context=context)
    # 3. 把页面数据存储成html文件，放入statics下
    prefix = os.path.dirname(os.path.dirname(settings.BASE_DIR))
    file_path = os.path.join(
        prefix,
        'statics/goods/%s.html' % sku.id   # sku.id: 1   ----> /statics/goods/1.html
    )
    with open(file_path, 'w') as f:
        f.write(html)


if __name__ == '__main__':
    # 获取所有sku商品
    skus = SKU.objects.all()
    # 分别静态化
    for sku in skus:
        print('正在静态化：', sku)
        generate_static_sku_detail_html(sku)

