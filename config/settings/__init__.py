import os
from .base import *

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'test':
    from .test import *
else:
    from .development import *