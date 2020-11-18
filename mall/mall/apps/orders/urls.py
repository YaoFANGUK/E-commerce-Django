from django.urls import path
from . import views

urlpatterns = [
    path('orders/settlement/', views.OrderSettlementView.as_view()),
]