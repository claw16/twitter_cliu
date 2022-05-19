from django.contrib.auth.models import User
from friendships.api.paginations import FriendshipPagination
from friendships.api.serializers import (
    FollowerSerializer,
    FollowingSerializer,
    FriendshipSerializerForCreate,
)
from friendships.models import Friendship
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


class FriendshipViewSet(viewsets.GenericViewSet):
    # 当method是POST的时候，程序会去查询当前class下的serializer_class或者get_serializer_class()
    # 如果都没有的话会报错
    serializer_class = FriendshipSerializerForCreate
    # 我们希望 POST /api/friendship/1/follow 是去 follow user_id=1 的用户
    # 因此这里 queryset 需要是 User.objects.all()
    # 如果是 Friendship.objects.all 的话就会出现 404 Not Found
    # 因为 detail=True 的 actions 会默认先去调用 get_object() 也就是
    # queryset.filter(pk=1) 查询一下这个 object 在不在
    queryset = User.objects.all()
    # 一般来说，不同的view所需要的pagination规则是不同的，一般都需要自定义
    pagination_class = FriendshipPagination

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        # 这里的 self.paginate_queryset() 先把 friendships 这个 queryset 传给
        # GenericAPIView 的 paginate_queryset, 它会去调用 PageNumberPagination 下的
        # paginate_queryset(queryset, request, self) 来返回请求页面的数据
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    # IsAuthenticated -> 如果没有登陆，会返回403 Forbidden
    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        # check if user id = ok exists, if not raise 400
        self.get_object()

        # from_user_id = request.user.id, to_user_id = pk
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'errors': 'You cannot follow yourself.',
            }, status=status.HTTP_400_BAD_REQUEST)

        # 特殊判断重复follow的情况，比如前端猛点follow
        # 静默处理，不报错
        if Friendship.objects.filter(
                to_user_id=pk,
                from_user_id=request.user.id).exists():
            return Response({
                'success': True,
                'duplicate': True,
            }, status=status.HTTP_201_CREATED)

        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': pk,
        })
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()  # 真的创建出来，相当于git commit
        return Response(
            FollowingSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        self.get_object()
        # 注意pk的类型是str，所以要做类型转换
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'errors': 'You cannot unfollow yourself.',
            }, status=status.HTTP_400_BAD_REQUEST)

        # https://docs.djangoproject.com/en/3.1/ref/models/querysets/#delete
        # Queryset的delete操作返回两个值，一个是删了多少数据，一个是具体每种类型删了多少
        # 为什么会出现多种类型数据的删除？因为可能foreign key设置了cascade级联删除
        # 比如A model的某个属性是B model的foreign key，并且设置了
        # on_delete=models.CASCADE，那当B的某个数据被删除的时候，A中的关联也会被删除
        # 所以CASCADE是很危险的，一般不用，而是用on_delete=models.SET_NULL
        # 这样可以避免误删除操作带来的多米诺效应
        deleted, _ = Friendship.objects.filter(
            from_user=request.user.id,
            to_user=pk,
        ).delete()
        return Response({'success': True, 'deleted': deleted})

