from django.db import models
from django import forms
from django.contrib.auth.models import User

STATUS_CODES = (
    (1, 'Open'),
    (2, 'In Progress'),
    (3, 'Closed'),
    (4, 'Deleted/Duplicate'),
    )

PRIORITY_CODES = (
    (1, 'High'),
    (2, 'Medium'),
    (3, 'Low'),
    )

REQUEST_CODES = (
    (1, 'Bug Report'),
    (2, 'Feature Request'),
    (3, 'Task Assignment'),
    (4, 'Improvement'),
    (5, 'Scope Reduction'),
    )

class Ticket(models.Model):
    """Ticket-based system for report/feature requests and bug filing"""
    title = models.CharField(max_length=50)
    description = models.TextField()
    authorized_users = models.ManyToManyField(User, null=True, blank=True, related_name='authorized_users')
    submitted_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    author = models.CharField(max_length=100)
    last_modified_by = models.CharField(max_length=100, blank=True, editable=False)
    assigned_to = models.ForeignKey(User, null=True, blank=True)
    status = models.IntegerField(default=1, choices=STATUS_CODES)
    priority = models.IntegerField(default=2, choices=PRIORITY_CODES)
    request_type = models.IntegerField(default=1, choices=REQUEST_CODES)
    attachments = models.ManyToManyField('TicketAttachment', null=True, blank=True, related_name='ticket_attachments')
    
    def assigned(self):
        return self.assigned_to != None

    class Meta:
        ordering = ('-submitted_date',)

    def __str__(self):
        return self.title

class TicketAttachment(models.Model):
    """Attachments for tickets."""
    attachment = models.FileField(upload_to="attachments/", help_text="(optional)")
    
    def __str__(self):
        return self.attachment.name.replace("attachments/", "")

class TicketAttachmentForm(forms.ModelForm):
    class Meta:
        model = TicketAttachment

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'priority', 'request_type')
