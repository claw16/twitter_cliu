class TweetPhotoStatus:
    PENDING = 0
    APPROVED = 1
    REJECTED = 2


# Use tuple of tuples in order to display the strings
# on the admin UI
TWEET_PHOTO_STATUS_CHOICES = (
    (TweetPhotoStatus.PENDING, 'Pending'),
    (TweetPhotoStatus.APPROVED, 'Approved'),
    (TweetPhotoStatus.REJECTED, 'Rejected'),
)
