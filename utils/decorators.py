from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def required_params(method='GET', params=None):
    # 当我们使用 @request_attr(params=['some_param']) 的时候
    # 这个 required_params() 函数应该返回一个 decorator 函数，它的参数
    # 就是被 @required_params 包裹起来的函数 view_func
    #
    # 从效果上来说，参数中写 params=[] 也没有太大问题，但是从好的编程习惯上来说
    # 函数的参数列表中的值不能是一个 mutable 的参数
    if params is None:
        params = []

    def decorator(view_func):
        # decorator 函数通过 wraps 来将 view_func 中的参数传递给 _wrapped_view
        # 这里的 instance 就是在 view_func 里的 self
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            if method.lower() == 'get':
                data = request.query_params
            else:
                data = request.data
            missing_params = [
                param for param in params if param not in data
            ]
            if missing_params:
                param_str = ','.join(missing_params)
                return Response({
                    'message': 'missing {} in request'.format(param_str),
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
            # 做完检测之后再去调用被 @required_params 包裹起来的 view_func
            return view_func(instance, request, *args, **kwargs)
        return _wrapped_view
    return decorator
