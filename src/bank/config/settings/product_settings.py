from .debug_settings import *



DEBUG = False

ALLOWED_HOSTS = [
    '*'
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'db',
        'USER': decouple.config("POSTGRES_USER"),
        'PASSWORD': decouple.config("POSTGRES_PASSWORD"),
        'HOST': 'postgres',
        'PORT': 5432,
    }
}