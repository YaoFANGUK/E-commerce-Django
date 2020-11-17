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
    # 退出登录
    path('logout/', views.LogoutView.as_view()),
    # 用户中心
    path('info/', views.UserInfoView.as_view()),
    # 添加邮箱
    path('emails/', views.EmailView.as_view()),
    # 用户浏览历史
    path('browse_histories/', views.UserBrowseHistory.as_view()),
    
]