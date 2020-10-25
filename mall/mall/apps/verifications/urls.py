from django.urls import path
from . import views

urlpatterns = [
    # 图形验证码
    path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
    # 短信验证码
    path('sms_codes/<mobile:mobile>/', views.SMSCodeView.as_view()),
    # 验证邮箱
    path('emails/verification/', views.VerifyEmailView.as_view()),
]