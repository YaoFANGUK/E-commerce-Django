from django.urls import path
from . import views

urlpatterns = [
    # 购物车管理
    path('carts/', views.CartsView.as_view()),
    # 全选/取消全选购物车
    path('carts/selection/', views.CartsSelectedAllView.as_view()),
    # 主页购物车简图展示
    path('carts/simple/', views.CartsSimpleView.as_view()),
]
