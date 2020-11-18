from django.urls import path
from . import views

urlpatterns = [
    # 省级地区
    path('areas/', views.ProvinceAreasView.as_view()),
    # 子级地区
    path('areas/<int:pk>/', views.SubAreasView.as_view()),
]
