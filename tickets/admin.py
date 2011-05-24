from django.contrib import admin
from tickets.models import Ticket, TicketAttachment

class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'submitted_date')
    list_filter = ('priority', 'status', 'request_type', 'submitted_date')
    search_fields = ('title', 'description',)
    save_on_top = True
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketAttachment)
