# backend/settings.py (部分設定)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'eco_app',  # 環保專案的應用
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'eco_db',
        'USER': 'eco_user',
        'PASSWORD': 'eva100422',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
