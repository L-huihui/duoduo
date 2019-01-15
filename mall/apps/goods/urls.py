from django.conf.urls import url
from . import views

urlpatterns = [
    #/goods/categories/
    url(r'^categories/$',views.CategoryView.as_view(),name='cagegories'),
]