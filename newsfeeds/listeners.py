def push_newsfeeds_to_cache(sender, instance, created, **kwargs)
    # if we changed the newsfeeds, it'll trigger post_save, because e.g.
    # newsfeed1.tweet = tweet1 -> newsfeed1.save()
    # but we only want to push new created newsfeeds to cache
    if not created:
        return

    from newsfeeds.services import NewsFeedService
    NewsFeedService.push_newsfeed_to_cache(instance)
