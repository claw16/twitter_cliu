from dateutil import parser
from django.conf import settings
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class EndlessPagination(BasePagination):
    page_size = 20

    def __init__(self):
        # super(xxx) explicitly specifies which parent class's __init__ is being called.
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def paginate_ordered_list(self, reverse_ordered_list, request):
        # reverse_ordered_list 是从 cache 得到的 obj list
        if 'created_at__gt' in request.query_params:  # 刷新最新内容的时候
            # Parse an ISO-8601 datetime string into a :class:`datetime.datetime`.
            created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            objects = []
            for obj in reverse_ordered_list:
                # get all objects created after created_at__gt
                if obj.created_at > created_at__gt:
                    objects.append(obj)
                else:
                    break
            self.has_next_page = False
            return objects

        index = 0
        if 'created_at__lt' in request.query_params:
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            for index, obj in enumerate(reverse_ordered_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                # if no object meets the requirements, return an empty list
                # NOTE: this is a for-else statement, not if-else
                reverse_ordered_list = []
        self.has_next_page = len(reverse_ordered_list) > index + self.page_size
        return reverse_ordered_list[index: index + self.page_size]

    def paginate_queryset(self, queryset, request, view=None):
        if 'created_at__gt' in request.query_params:
            """
            用于下拉刷新的时候加载最新的内容进来，为了简要，下拉刷新不做翻页机制，
            而是直接加载所有更新的数据。
            """
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset.order_by('-created_at')

        if 'created_at__lt' in request.query_params:
            """
            用于向上划动屏幕（向下翻页）时加载下一页的数据
            查询符合条件的 （created_at < created_at__lt）的，按照时间倒序排列的，
            前 size + 1 个 objects。+1 的原因是可以用来判断是否有下一页
            """
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginate_cached_list(self, cached_list, request):
        # Video 097
        paginated_list = self.paginate_ordered_list(cached_list, request)
        # 如果是上翻页，paginated_list 里是所有的最新暑假，直接返回
        if 'created_at__gt' in request.query_params:
            return paginated_list
        # 如果还有下一页，说明 cached_list 里面的数据还没取完，也直接返回
        if self.has_next_page:
            return paginated_list
        # 如果 cached_list 的长度不组最大限制，说明 cached_list 里已经是所有数据了
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        # 如果进入这里，说明可能存在在数据库里没有 load 进 cache 的数据，需要直接去数据库查询
        return None

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        })
