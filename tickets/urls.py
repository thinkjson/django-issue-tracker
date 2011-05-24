from django.conf.urls.defaults import *

urlpatterns = patterns('tickets.views',
    (r'^$', 'list_tickets'),
    (r'^show/(?P<ticket_id>\d{1,6})/$', 'show_ticket'),
    (r'^show/(?P<ticket_id>\d{1,6})/attach/$', 'add_attachment'),
    (r'^show/(?P<ticket_id>\d{1,6})/detach/(?P<attachment_id>\d{1,6})$', 'remove_attachment'),
    (r'^show/(?P<ticket_id>\d{1,6})/add_user/$', 'add_user'),
    (r'^show/(?P<ticket_id>\d{1,6})/remove_user/$', 'remove_user'),
    (r'^add/', 'add_ticket' ),
    (r'^notes/', include('django.contrib.comments.urls')),
)
