from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class EndlessPagination(BasePagination):
    page_size = 20

    def __init__(self):
        # TODO: why super here?
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

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

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        })
