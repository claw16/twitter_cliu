from tweets.models import Tweet, TweetPhoto
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_helper import RedisHelper


class TweetService(object):
    @classmethod
    def create_photo_from_files(cls, tweet, files):
        photos = []
        for i, file in enumerate(files):
            photo = TweetPhoto(
                tweet=tweet,
                file=file,
                order=i,
                user=tweet.user,
            )
            photos.append(photo)
        TweetPhoto.objects.bulk_create(photos)

    @classmethod
    def get_cached_tweets(cls, user_id):
        # Here queryset = xxx hasn't really queried the db because Queryset uses lazy loading
        # If we iterate over a queryset, e.g. list(queryset) or do_something for x in queryset
        # will really query the DB
        queryset = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_TWEETS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_tweet_to_cache(cls, tweet):
        # Queryset is lazy loading
        queryset = Tweet.objects.filter(user_id=tweet.user_id).order_by('-created_at')
        key = USER_TWEETS_PATTERN.format(user_id=tweet.user_id)
        RedisHelper.push_object(key, tweet, queryset)
