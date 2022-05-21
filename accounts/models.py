from accounts.listeners import user_changed, profile_changed
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete


class UserProfile(models.Model):
    # One-to-one field creates a unique index, every UserProfile <-> User pair is unique
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    # Django 还有一个 ImageField，但是尽量不要用，会有很多的其他问题，用 FileField 可以起到
    # 同样的效果。因为最后我们都是以文件形式存储起来，使用的是文件的 url 进行访问
    # 当一个 user 被创建之后，会创建一个 user profile 的 object
    # 此时用户还来不及去设置 nickname 等信息，因此设置 null=True
    avatar = models.FileField(null=True)
    nickname = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)


# 定义一个 profile 的 property 方法，植入到 User 这个 model 里
# 这样当我们通过 user 的一个实例化对象访问 profile 的时候，即 user_instance.profile
# 就会在 UserProfile 中进行 get_or_create 来获得对应的 profile 的 object
# 这种写法实际上是一个利用 Python 的灵活性进行 hack 的方法，这样会方便我们通过 user 快速
# 访问到对应的 profile 信息。
def get_profile(user: User):
    # import inside the function to avoid loop dependency
    from accounts.services import UserService
    # 如果多次对这个 object 调用，就不需要重复的查询数据库
    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    # 这里用 get_or_create 是因为有可能某个 user 并没有 profile，所以 get 不到
    # 对于这种 user，我们给它创建一个空 profile
    # profile, _ = UserProfile.objects.get_or_create(user=user)
    profile = UserService.get_profile_through_cache(user.id)
    # 使用 user 对象的属性进行 cache，避免多次调用同一个 user 的 profile 时对数据库重复查询
    setattr(user, '_cached_user_profile', profile)
    return profile


# 给 User Model 增加了一个 profile 的 property 方法用于快捷访问
# Python 在运行的时候会 load 所有的project中的脚本，这句话就会被执行，然后就会吧这个 profile
# 加入 User model。
# 相当于给 User model 增加了一个 profile property。我们没有直接去 User 里面增加这个property
# 是因为 User model 用的是 Django 自带的，不属于这个 project 的一部分。等效于：
# class User:
#     @property
#     def profile(self):
#         get_profile()
User.profile = property(get_profile)

# hook up with listeners to invalidate cache
pre_delete.connect(user_changed, sender=User)
post_save.connect(user_changed, sender=User)

pre_delete.connect(profile_changed, sender=UserProfile)
post_save.connect(profile_changed, sender=UserProfile)
