from django.urls import path
from . import views

urlpatterns = [
    path('payment/<int:order_id>/', views.PaymentView.as_view()),
    # 处理支付成功的回调： PUT
    path('payment/status/', views.PaymentStatusView.as_view()),
]
