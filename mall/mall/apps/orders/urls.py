from django.urls import path
from . import views

urlpatterns = [
    path('orders/settlement/', views.OrderSettlementView.as_view()),
    # 提交订单接口
    path('orders/commit/', views.OrderCommitView.as_view()),
]