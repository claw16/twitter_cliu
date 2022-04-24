from comments.api.permissions import IsObjectOwner
from comments.models import Comment
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny


class CommentViewSet(viewsets.GenericViewSet):
    # 只实现 list, create, update, destroy 的方法
    # 不实现 retrieve （查询单个comment） 的方法，因为没有这个需求
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()

    def get_permissions(self):
        """
        注意要加用 AllowAny() / IsAuthenticated() 实例化出对象
        而不是 AllowAny / IsAuthenticated 这样只是一个类名
        """
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['destroy', 'update']:
            # 这里会按照list里面的顺序进行验证，假如IsAuthenticated验证没有通过
            # 就不再继续后面的IsObjectOwner的验证
            # 这里如果不加IsAuthenticated，结果也是一样的
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }
        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save 方法会触发 serializer 里的 create 方法，点进 save 的具体实现里可以看到
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        # get_object() 是 DRF 包装的函数，找不到的时候会 raise 404 error
        # 所以这里无需额外判断
        # get_object() 会根据request里面的URL和class里面的queryset来filter所需要的object
        comment = self.get_object()
        serializer = CommentSerializerForUpdate(
            instance=comment,
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        # save 方法会出发 serializer 里的 update 方法，点进 save 的具体实现里可以看到
        # save 是根据 instance 参数有没有传来决定是出发 create 还是 update
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        # DRF 里默认 destroy 返回的是 status = 204 no content
        # 这里 return了success=True 更直观地让前端判断，所以 200 更合适
        return Response({'success': True}, status=status.HTTP_200_OK)
