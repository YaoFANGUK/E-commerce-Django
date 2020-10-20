from django.urls import path
from . import views


# 路由映射表
urlpatterns = [
    # 路由映射公式： 请求方法 + 请求路径 = 视图方法
    path('register/', views.RegisterView.as_view()),
    path('usernames/<username:username>/count/', views.UsernameCountView.as_view()),
    path('mobiles/<mobile:mobile>/count/', views.MobileCountView.as_view()),
]