from django.conf.urls import url

from orders import views

urlpatterns = [
    #/orders/places/
    url(r'^places/$',views.OrderSettlementView.as_view(),name='placeorder'),
    url(r'^$', views.OrderView.as_view(), name='commitorder'),
    url(r'^order/$', views.UserCenterOrdersView.as_view()),
    url(r'^(?P<order_id>\d+)/uncommentgoods/$', views.CommentListView.as_view()),
    url(r'^(?P<order_id>\d+)/comments/$', views.CommentView.as_view()),
    url(r'^details/(?P<sku_id>\d+)/comments/$', views.CommentDetailView.as_view()),
]