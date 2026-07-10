from django.conf import settings
from hashids import Hashids

from foodgram_backend.constants import HASHIDS_MIN_LENGTH

hashids = Hashids(salt=settings.SECRET_KEY, min_length=HASHIDS_MIN_LENGTH)
