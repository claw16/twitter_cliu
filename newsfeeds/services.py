from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService(object):
    @classmethod
    def fanout_to_followers(cls, tweet):
        # wrong method:
        # Don't put DB operations in a for loop - low efficiency
        # for follower in FriendshipService.get_followers(tweet.user):
        #     NewsFeed.objects.create(
        #         user=follower,
        #         tweet=tweet,
        #     )

        # a good practice:
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in FriendshipService.get_followers(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)

        # bulk create 不会出发 post_save 的 signal，所以需要手动存入 cache
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        # 这里真正要存入 cache 的是 newsfeed，是要把新的 newsfeed 存入对应用户的 newsfeeds list
        # 因为有可能存的时候 newsfeeds list 已经过期了，这时候我们需要把整个 queryset 取到的 newsfeeds
        # 全部存入 cache，这其中也包括了当前的 newsfeed。如果当前用户的 newsfeeds list 没有过期，
        # 直接 serialize 当前的 newsfeed 然后 lpush 进 cache 就行了。
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)
