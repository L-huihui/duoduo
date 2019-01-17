from django.conf.urls import url
from . import views

urlpatterns = [
    #/goods/categories/
    url(r'^categories/$',views.CategoryView.as_view(),name='cagegories'),
    # /goods/categories/(?P<category_id>\d+)/hotskus/
    url(r'^categories/(?P<category_id>\d+)/hotskus/$', views.HotSKUListView.as_view(), name='hot'),
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view(), name='list'),

]