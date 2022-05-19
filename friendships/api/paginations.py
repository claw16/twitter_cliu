from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FriendshipPagination(PageNumberPagination):
    # default page size, i.g. no page size specified in url
    page_size = 20
    # default page_size_query_param == None, forbidding client specify page size
    # if we enable page_size_query_param, clients can use `size=10` to fit
    # different use cases, e.g. requirements for page size of web/mobile are different
    # e.g. /api/friendships/3/followers/?page=2&size=20
    page_size_query_param = 'size'
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'total_results': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page_number': self.page.number,
            'has_next_page': self.page.has_next(),
            'results': data,
        })
