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
    # 新增收货地址
    path('addresses/create/', views.CreateAddressView.as_view()),
    # 展示收获地址
    path('addresses/', views.AddressView.as_view()),
    # 修改和删除收货地址
    path('addresses/<int:address_id>/', views.UpdateDestroyAddressView.as_view()),
    # 设置默认地址
    path('addresses/<int:address_id>/default/', views.DefaultAddressView.as_view()),
    # 修改地址标题
    path('addresses/<int:address_id>/title/', views.UpdateTitleAddressView.as_view()),
    # 修改密码
    path('password/', views.ChangePasswordView.as_view()),
]
