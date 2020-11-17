from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from users.models import User
from django_redis import get_redis_connection
import json, re
from django.contrib.auth import authenticate, login, logout
from django.db import DatabaseError
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url
from mall.utils.secret import SecretOauth
from goods.models import SKU
from .models import Address


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '访问数据库失败'
            }, status=400)
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '访问数据库失败'
            }, status=400)
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })


class RegisterView(View):
    """用户注册业务逻辑"""

    def post(self, request):
        '''接收参数， 保存到数据库'''
        # 1. 接收参数： 请求体中的JSON数据 request.body
        json_bytes = request.body  # 从请求体中获取原始的JSON数据， bytes类型
        json_str = json_bytes.decode()  # 将字节流转换为字符串
        json_dict = json.loads(json_str)  # 将JSON字符串转换为python标准字典

        # 2. 提取参数
        username = json_dict.get('username')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        mobile = json_dict.get('mobile')
        allow = json_dict.get('allow')
        sms_code = json_dict.get('sms_code')

        # 3. 参数校验
        # 3.1 必要性校验
        if not all([username, password, password2, mobile, sms_code]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要的参数'
            }, status=400)

        # 3.2 约束条件校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名格式有误'
            }, status=400)

        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            }, status=400)

        if password != password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '两次输入的密码不一致'
            }, status=400)

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': '手机号格式有误'
            }, status=400)

        if allow != True:
            return JsonResponse({
                'code': 400,
                'errmsg': '用户未同意注册协议'
            }, status=400)

        # 3.3 业务性校验
        # 保存注册数据之前，对比短信验证码
        # 判断短信验证码是否正确：与图形验证码一样的业务逻辑
        #   提取服务端存储的短信验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        # 判断短信验证码是否过期
        if not sms_code_server:
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码失效'
            }, status=400)
        # 对比用户输入的和服务器存储的短信验证码是否一致
        if sms_code != sms_code_server.decode():
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码有误'
            }, status=400)

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'errmsg': '注册失败'
            }, status=500)

        # 状态保持 —— 使用session机制，把用户数据写入redis
        login(request, user)

        # 4. 构建响应
        # 生成响应对象
        response = JsonResponse({
            'code': 0,
            'errmsg': '注册成功'
        })
        # 在响应对象中谁用户名信息
        # 将用户名写入到cookie，有效期14天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response


class LoginView(View):
    """用户登录后端逻辑"""

    def post(self, request):
        """实现登陆接口"""
        # 1. 接收参数
        data_dict = json.loads(request.body.decode())
        username = data_dict.get('username')
        password = data_dict.get('password')
        remembered = data_dict.get('remembered')
        # 2. 参数校验
        if not all([username, password]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要的参数'
            }, status=400)
        # 3.验证是否能够登陆
        user = authenticate(request, username=username, password=password)

        # 判断是否为空，如果为空，返回
        if user is None:
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名或密码错误'
            }, status=400)

        # 4. 状态保持
        login(request, user)

        # 5. 判断是否记住用户
        if remembered != True:
            # 7. 如果没有记住，session立即失效
            request.session.set_expiry(0)
        else:
            # 6.如果记住：session有效期设置为两周
            request.session.set_expiry(None)

        # 8. 返回json response
        # 生成响应对象
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        # 在响应对象中谁用户名信息
        # 将用户名写入到cookie，有效期14天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response


class LogoutView(View):
    """
    实现退出登录的接口
    """

    def delete(self, request):
        """
        实现退出登录逻辑
        """
        # 清理session
        logout(request)
        # 创建response对象
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        # 调用对象的delete_cookie方法，清楚cookie
        response.delete_cookie('username')
        # 返回响应
        return response


class UserInfoView(LoginRequiredJSONMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息页面"""
        info_data = {
            "username": request.user.username,
            "mobile": request.user.mobile,
            "email": request.user.email,
            "email_active": request.user.email_active
        }
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'info_data': info_data
        })


class EmailView(View):
    """
    添加邮箱
    """

    def put(self, request):
        """
        实现添加邮箱逻辑
        """
        # 1.提取参数
        data = json.loads(request.body.decode())
        email = data.get('email')
        # 2.校验参数
        if not email:
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少参数'
            })
        if not re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return JsonResponse({
                'code': 400,
                'errmsg': '邮箱格式有误'
            })
        # 3.业务处理 —— 修改email属性和发送验证邮件
        try:
            user = request.user
            user.email = email
            user.save()
        except DatabaseError:
            return JsonResponse({
                'code': 500,
                'errmsg': '数据库添加邮箱失败'
            }, status=500)
        # 发送验证邮件 使用celery异步实现
        # 调用发送的函数
        verify_url = generate_verify_email_url(request)
        send_verify_email.delay(email, verify_url)

        # 4.构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': '添加邮箱成功'
        })


class UserBrowseHistory(LoginRequiredMixin, View):
    # 用户浏览历史记录
    def post(self, request):
        # 1. 提取参数
        user = request.user
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        # 2. 校验参数
        try:
            sku = SKU.objects.get(pk=sku_id, is_launched=True)
        except DatabaseError:
            # 如果sku商品不存在或已经下架，则不记录历史
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok',
            })
        # 3. 业务数据处理 - 历史记录写入redis
        # history_1 : [1,2,3,4,5]
        conn = get_redis_connection('history')  # 3号库
        p = conn.pipeline()
        # (1).去重
        p.lrem('history_%s' % user.id, 0, sku_id)
        # (2).左侧插入
        p.lpush('history_%s' % user.id, sku_id)
        # (3).截断
        p.ltrim('history_%s' % user.id, 0, 4)
        p.execute()
        # (4).构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
        })

    # 查询历史记录
    def get(self, request):
        # 1.提取参数
        user = request.user
        # 2.校验参数
        # 3.业务处理 —— 从redis读历史记录，再从mysql读详细信息
        # 3.1 读取redis历史(访问sku_id)
        conn = get_redis_connection('history')  # 3号库
        sku_ids = conn.lrange('history_%s' % user.id, 0, -1)
        # 3.2读取mysql商品详细信息
        # django模型类根据主键过滤的时候，主键可以直接传递整数、字符或者字节
        skus = SKU.objects.filter(
            # 过滤出id包含在sku_ids列表中的所有对象
            # id 在 [b'1', b'2', b'3']
            id__in=sku_ids
        )
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        # 构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'skus': sku_list
        })


class CreateAddressView(LoginRequiredJSONMixin, View):
    """
    新增地址
    """

    def post(self, request):
        """
        实现新增地址逻辑
        """
        # 获取地址个数：
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        # 判断书否超过地址上限： 最多20个
        if count >= 20:
            return JsonResponse({
                'code': 400,
                'errmsg': '超过地址数量上限',
            })
        # 1. 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            })
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数mobile有误'
            })
        if tel:
            if not re.match(r'(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({
                    'code': 400,
                    'errmsg': '参数tel有误'
                })
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({
                    'code': 400,
                    'errmsg': '参数email有误'
                })
        try:
            address = Address.objects.create(
                user=request.user,  # 当前新增地址从属用户
                title=receiver,  # 新增的时候把收件人名称作为默认地址标题
                receiver=receiver,  # 收货人别名
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '新增地址失败'
            })

        # 新增地址成功，将新增地址响应给前端实现局部刷新
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        # 返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': '新增地址成功',
            'address': address_dict
        })


class AddressView(View):
    """
    用户收货地址展示
    """

    def get(self, request):
        """
        提供地址管理界面
        """
        # 获取所有的地址：
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 创建空的列表
        address_dict_list = []
        # 遍历
        for address in addresses:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email
            }
            if address.id == request.user.default_address_id:
                # 当前地址是用户默认地址，需要把这个地址插入列表头
                address_dict_list.insert(0, address_dict)
            else:
                address_dict_list.append(address_dict)
        # 获取默认地址id
        default_id = request.user.default_address_id

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'addresses': address_dict_list,
            'default_address_id': default_id
        })


class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
    """
    修改和删除地址
    """

    def put(self, request, address_id):
        """
        修改地址
        """
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            })

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数mobile有误'
            })

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({
                    'code': 400,
                    'errmsg': '参数tel有误'
                })

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({
                    'code': 400,
                    'errmsg': '参数email有误'
                })

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '更新地址失败'
            })

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return JsonResponse({
            'code': 0,
            'errmsg': '更新地址成功',
            'address': address_dict
        })

    def delete(self, request, address_id):
        """
        删除地址
        """
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)
            # 将地址逻辑删除设置为true
            address.is_deleted = True
            address.save()
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '删除地址失败'
            })
        # 返回删除地址结果响应
        return JsonResponse({
            'code': 0,
            'errmsg': '删除地址成功'
        })


class DefaultAddressView(View):
    """
    设置默认地址
    """
    def put(self,request, address_id):
        """
        设置默认地址
        """
        try:
            # 接收参数，查询地址
            address = Address.objects.get(id=address_id)
            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '设置默认地址失败'
            })
        return JsonResponse({
            'code': 0,
            'errmsg': '设置默认地址成功'
        })


class UpdateTitleAddressView(View):
    """
    设置地址标题
    """
    def put(self, request, address_id):
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        try:
            # 查询地址
            address = Address.objects.get(id=address_id)
            # 设置新的地址标题
            address.title = title
            address.save()
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '设置地址标题失败'
            })
        # 响应删除地址结果
        return JsonResponse({
            'code': 0,
            'errmsg': '设置地址标题成功'
        })


class ChangePasswordView(View):
    """
    修改密码
    """
    def put(self, request):
        """
        实现修改密码逻辑
        """
        # 接收参数
        data_dict = json.loads(request.body.decode())
        old_password = data_dict.get('old_password')
        new_password = data_dict.get('new_password')
        new_password2 = data_dict.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            })

        result = request.user.check_password(old_password)
        if not result:
            return JsonResponse({
                'code': 400,
                'errmsg': '原始密码不正确'
            })

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码最少为8位，最长20位'
            })
        if new_password != new_password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '两次输入的密码不一致'
            })

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except DatabaseError:
            return JsonResponse({
                'code': 400,
                'errmsg': '修改密码失败'
            })
        # 清理状态保持信息
        logout(request)
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.delete_cookie('username')
        # 响应修改密码结果：重定向到登陆界面
        return response

