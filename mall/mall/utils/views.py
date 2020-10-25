from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class LoginRequiredJSONMixin(LoginRequiredMixin):
    """
    自定义LoginRequiredMixin
    如果用户未登陆，响应json，且状态码为400
    """
    def handle_no_permission(self):
        return JsonResponse({
            'code':400,
            'errmsg': '用户未登陆'
        })
