from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler
from ratelimit.exceptions import Ratelimited


def exception_handler(exc, context):
    # Call REST framework's default exception handler first
    # to get the standard error response
    response = drf_exception_handler(exc, context)

    # Then change the HTTP status code and message to the response
    # if it's a `Ratelimited instance
    if isinstance(exc, Ratelimited):
        response.data['detail'] = 'Too many requests, try again later.'
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS

    return response
