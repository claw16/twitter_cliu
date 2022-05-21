def user_changed(sender, instance, **kwargs):
    # import inside function to avoid loop dependency
    from accounts.services import UserService
    UserService.invalidate_user(instance.id)


def profile_changed(sender, instance, **kwargs):
    # import inside function to avoid loop dependency
    from accounts.services import UserService
    # 这里不是 id 而是 user_id，id 对应的是 profile，我们需要清除的是 user_id
    UserService.invalidate_profile(instance.user_id)
