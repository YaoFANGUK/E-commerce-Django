from django.shortcuts import render
from django.views import View
from .utils import *


class IndexView(View):
    """
    首页广告
    """

    def get(self, request):
        """
        提供首页广告界面
        """
        categories = get_categories()

        # 广告数据
        contents = get_contents()

        # 渲染模板上下文
        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request=request, template_name='index.html', context=context)
