"""
Django settings for twitter project.

Generated by 'django-admin startproject' using Django 3.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 't3ku3pa#9ynw(g3lc_)u*og8s!l!j51x+d@cg7t9@3c!2@yk5)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '172.17.0.1']
# INTERNAL_IPS
INTERNAL_IPS = ['127.0.0.1', 'localhost', '172.17.0.1']

# Application definition

INSTALLED_APPS = [
    # django default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    # third-party packages
    'django_filters',
    'debug_toolbar',
    'notifications',
    'rest_framework',
    # project apps
    'accounts',
    'comments',
    'friendships',
    'likes',
    'newsfeeds',
    'tweets',
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend', ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'twitter.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'twitter.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'twitter',
        'HOST': '0.0.0.0',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': 'liuchao9',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# media 的作用适用于存放被用户上传的文件信息
# 当我们使用默认 FileSystemStorage 作为 DEFAULT_FILE_STORAGE 的时候
# 文件会被默认上传到 MEDIA_ROOT 指定的目录下
# media 和 static 的区别是：
# - static 里通常是 css,js 文件之类的静态代码文件，是用户可以直接访问的代码文件
# - media 里使用户上传的数据文件，而不是代码
MEDIA_ROOT = 'media/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

# 设置存储用户上传文件的 storage 文件系统
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'  # AWS S3
# 测试环境用本地文件系统
is_testing = ((' '.join(sys.argv)).find('manage.py test') != -1)
if is_testing:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'  # local file storage

# 把本地的设置，例如debug配置，放入local_settings.py，不push到remote repo
# 这样在production环境中不会引入这些设置
try:
    from .local_settings import *
except:
    pass
