from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from areas.models import Area
from django.db import DatabaseError

class ProvinceAreasView(View):
    """省级地区"""
    def get(self, request):
        """
        提供省级地区数据:
        1. 查询省级数据
        2. 序列化省级数据
        3. 响应省级数据
        """
        try:
            # 1.查询省级数据
            province_model_list = Area.objects.filter(parent__isnull=True)
            # 2.整理省级数据
            province_list = []
            for province_model in province_model_list:
                province_list.append({
                    'id': province_model.id,
                    'name': province_model.name
                })
        except DatabaseError as e:
            return JsonResponse({
                'code': 500,
                'errmsg': '数据库获取省份数据失败'
            })

        # 3.返回整理好后的数据
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'province_list': province_list
        })



