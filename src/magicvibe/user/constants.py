from datetime import timedelta

MIN_PROFILE_AGE = 18
MAX_PROFILE_AGE = 100
MAX_PROFILE_NAME_LENGTH = 64
MAX_BIO_LENGTH = 500

# `last_seen_at` is written at most once per this interval per user.
LAST_SEEN_UPDATE_INTERVAL = timedelta(minutes=1)
