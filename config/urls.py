from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [path("api/v1/auth/token/", obtain_auth_token, name="api-token")]
