"""
定义一个函数，用来实现渲染完整index.html静态化页面
"""
import os
from django.conf import settings
from django.template import loader
from .utils import *
from content.models import ContentCategory


# 需要定时执行该函数
def generate_static_index_html():
    # 1.构建模板参数 —— 动态数据
    categories = get_categories()  # 用来渲染页面的三级分类
    contents = get_contents()  # 广告数据
    context = {
        'categories': categories,
        'contents': contents,
    }

    # 2.页面渲染
    # 2.1 获取模板对象
    template = loader.get_template('index.html')
    # 2.2 传入动态数据，渲染出完整的页面数据
    html = template.render(context=context)  # render函数返回渲染出来的html文件
    # 3. 把完整的页面数据保存成静态文件index.html，存放在statics里面
    prefix = os.path.join(
        os.path.dirname(os.path.dirname(settings.BASE_DIR)),
        'statics'
    )
    file_path = os.path.join(prefix, 'index.html')
    with open(file_path, 'w') as f:
        f.write(html)
