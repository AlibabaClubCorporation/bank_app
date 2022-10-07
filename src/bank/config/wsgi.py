"""
WSGI config for bank project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import decouple

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'config.settings.{decouple.config("CONFIGURATION_FILE_TYPE")}_settings')

application = get_wsgi_application()
