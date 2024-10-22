# coding:utf-8
"""
Django settings for myforum project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

ENABLE_SSL = False

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# from sae.const import (MYSQL_HOST, MYSQL_HOST_S, MYSQL_PORT, MYSQL_USER,
#                        MYSQL_PASS, MYSQL_DB)
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': MYSQL_DB,
#         'USER': MYSQL_USER,
#         'PASSWORD': MYSQL_PASS,
#         'HOST': MYSQL_HOST,
#         'PORT': MYSQL_PORT,
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(@e7r3+4ovf3r(%25s7@71xtx-yyp^(wqgl85%a5zzfu%rxr0r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'forum',
    #django应用forum（自己新创建，且这里比较特别的是：
    #当前“指针”直接落于forum页面处，迁移时使用python manage.py makemigrations即可（接着使用migrate创建新定义的模型的数据表））
    #迁移是非常强大的功能，它能让你在开发过程中持续的改变数据库结构而不需要重新删除和创建表 - 它专注于使数据库平滑升级而不会丢失数据。
    #我们会在后面的教程中更加深入的学习这部分内容，现在，你只需要记住，改变模型需要这三步：
    #编辑 models.py 文件，改变模型。
    #运行 python manage.py makemigrations 为模型的改变生成迁移文件。
    #运行 python manage.py migrate 来应用数据库迁移。
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ############################## 自定义中间件 ################################
    'forum.middle.CommonMiddleware',
)

ROOT_URLCONF = 'myforum.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'forum', 'templates'), ],
        "APP_DIRS": True,
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

WSGI_APPLICATION = 'myforum.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

AUTH_USER_MODEL = "forum.LoginUser"

# 会话(登录)超时设置
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 60 * 10

# cache配置#########################################
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'options': {
            'MAX_ENTRIES': 1024,
        }
    },
    #    'memcache': {
    #        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #        #'LOCATION': 'unix:/home/billvsme/memcached.sock',
    #        'LOCATION': '127.0.0.1:11211',
    #        'options': {
    #            'MAX_ENTRIES': 1024,
    #        }
    #    },
}

# email配置#########################################
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.126.com'  # SMTP地址 例如: smtp.163.com
EMAIL_PORT = 25  # SMTP端口 例如: 25
EMAIL_HOST_USER = 'Psq147258@126.com'  # 我自己的邮箱 例如: xxxxxx@126.com
EMAIL_HOST_PASSWORD = ''  # SMTP密码 例如  xxxxxxxxx
# EMAIL_SUBJECT_PREFIX = u'v'       #为邮件Subject-line前缀,默认是'[django]'
EMAIL_USE_TLS = True  # 与SMTP服务器通信时，是否启动TLS链接(安全链接)。默认是false

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

X_FRAME_OPTIONS = 'SAMEORIGIN'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
