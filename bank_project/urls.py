from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Django's built-in full model-management admin
    path('', include('accounts.urls')),
]
