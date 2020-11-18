from django.urls import path
from . import views

urlpatterns = [
    # 首页商品频道分类数据
    path('', views.IndexView.as_view()),
]
