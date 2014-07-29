from django.conf.urls import patterns, url
from .views import MainView, EntityView, NewEntityView, UpdateEntityView

urlpatterns = patterns('',
    url(r'^$', MainView.as_view(), name="show_all"),
    url(r'^(?P<entity>\w+)$', EntityView.as_view(), name="show_entity"),
    url(r'^(?P<entity>\w+)/add', NewEntityView.as_view(), name="new_entity"),
    url(r'^(?P<entity>\w+)/update/(?P<pk>\d+)$', UpdateEntityView.as_view(), name="update_entity"),
)
