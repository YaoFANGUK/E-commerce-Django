"""
封装首页商品频道分类
"""
from collections import OrderedDict
from goods.models import GoodsChannel
from content.models import ContentCategory


def get_categories():
    """
    提供商品频道和分类
    :return 菜单字典
    """
    # 查询商品频道和分类
    # 1.构建模板参数
    categories = OrderedDict()  # 商品分类频道
    # 按照组id排序，再按照sequence排序
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    # 遍历每一个频道，把频道插入以"组id"为键的键值对中
    for channel in channels:
        # 当前租不存在的时候(第一次构建)
        group_id = channel.group_id  # 当前组

        if group_id not in categories:
            categories[group_id] = {
                'channels': [],  # 一级分类
                'sub_cats': []  # 二级分类
            }
        cat1 = channel.category  # 当前频道的类别

        # 追加当前频道
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 构建当前类别的子类别
        # 二级分类
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)

    return categories


def get_contents():
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')
    return contents
