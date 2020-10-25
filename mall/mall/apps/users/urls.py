from django.urls import path
from . import views

urlpatterns = [
    # 判断用户名是否重复
    path('usernames/<username:username>/count/', views.UsernameCountView.as_view()),
    # 判断手机号是否重复
    path('mobiles/<mobile:mobile>/count/', views.MobileCountView.as_view()),
    # 用户注册
    path('register/', views.RegisterView.as_view()),
    # 用户登录
    path('login/', views.LoginView.as_view()),
]