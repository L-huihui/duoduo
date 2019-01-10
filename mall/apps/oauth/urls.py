from django.conf.urls import url
from .views import OAuthQQURLView
urlpatterns = [
    url(r'^qq/statues/$', OAuthQQURLView.as_view())
]