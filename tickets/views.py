from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from tickets.models import *
from django.contrib.comments.signals import comment_was_posted
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import RequestContext
from django.db.models import Q
from django.db.models.signals import post_save
from django.contrib.admin.models import LogEntry

@login_required
def list_tickets(request):
    """Show a list of all tickets of which you are listed as an authorized user"""
    tickets = Ticket.objects.filter(Q(authorized_users=request.user) | Q(assigned_to=request.user))\
        .exclude(status=4).distinct('id')
    if request.is_ajax():
        json = serializers.serialize("json", tickets)
        return HttpResponse(json, mimetype="application/json")
    else:
        return render_to_response("tickets/list_tickets.html",
            { 'tickets': tickets, 'title': "Tickets", "request": request },
            context_instance=RequestContext(request))

@login_required
def show_ticket(request, ticket_id):
    """Shows an individual ticket."""
    ticket = Ticket.objects.filter( Q(pk=ticket_id), \
        Q(authorized_users=request.user) | Q(assigned_to=request.user) ).distinct('id')
    if ticket.count() == 0:
        raise Http404
    else:
        ticket = ticket[0]
    available_users = User.objects.filter(is_active=True).exclude(authorized_users=ticket.id).order_by("first_name", "username")
    if request.is_ajax():
        template = "tickets/xhr.html"
    else:
        template = "base.html"
    return render_to_response("tickets/view_ticket.html", { 
        'ticket': ticket,
        'available_users': available_users,
        'title': ("Tickets - %s" % ticket.title),
        'template': template
        },
        context_instance=RequestContext(request))

@login_required
def add_ticket(request):
    """Allows users to add their own tickets on the frontend. Not all fields are available."""
    if request.method == 'POST':
        form = TicketForm(request.POST)
        attachment = TicketAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.get_full_name():
                ticket.author = request.user.get_full_name()
            else:
                ticket.author = request.user.username
            ticket.save()
            ticket.authorized_users.add(request.user)
            form.save_m2m()
            if attachment.is_valid():
                new_attachment = attachment.save()
                ticket.attachments.add(new_attachment)
            return HttpResponseRedirect( reverse('tickets.views.show_ticket', kwargs={'ticket_id': ticket.id}) )
    else:
        form = TicketForm()
        attachment = TicketAttachmentForm()
    return render_to_response('tickets/add_ticket.html', { 
        'title': 'Tickets - New Ticket',
        'form':form, 'attachment': attachment },
        context_instance=RequestContext(request))

@login_required
def add_attachment(request, ticket_id):
    """Allows a user to attach a file to their ticket for review."""
    ticket = get_object_or_404(Ticket, id=ticket_id);
    if request.method == 'POST':
        form = TicketAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.ticket_id=ticket_id
            attachment = form.save()
            ticket.attachments.add(attachment)
            return HttpResponseRedirect( reverse('tickets.views.show_ticket', kwargs={'ticket_id': ticket_id}) )
    else:
        form = TicketAttachmentForm()
    return render_to_response('tickets/add_attachment.html', 
        { 'title': 'Tickets - Attach File', 'ticket_name': ticket.title, 'form':form },
                          context_instance=RequestContext(request))

@login_required
def add_user(request, ticket_id):
    """Allows a user to add another authorized user on a ticket."""
    if "user" in request.POST:
        user = User.objects.get(id=request.POST["user"])
        Ticket.objects.get(id=ticket_id).authorized_users.add(user)
    return HttpResponseRedirect( reverse('tickets.views.show_ticket', kwargs={'ticket_id': ticket_id}) )

@login_required
def remove_user(request, ticket_id):
    """Allows a user to remove another authorized user on a ticket, including themselves."""
    if "user" in request.POST:
        user = User.objects.get(id=request.POST["user"])
        Ticket.objects.get(id=ticket_id).authorized_users.remove(user)
    return HttpResponseRedirect( reverse('tickets.views.show_ticket', kwargs={'ticket_id': ticket_id}) )

@login_required
def remove_attachment(request, ticket_id, attachment_id):
    """Allows a user to remove an attachment from a ticket."""
    #try:
    attachment = TicketAttachment.objects.get(pk=attachment_id)
    attachment.delete()
    #except Exception:
    #    pass
    return HttpResponseRedirect( reverse('tickets.views.show_ticket', kwargs={'ticket_id': ticket_id}) )

def notify_users(sender, **kwargs):
    if 'comment' in kwargs and kwargs['comment'].content_object.__class__.__name__ == "Ticket":
        if kwargs['comment'].comment.strip() == "":
            kwargs['comment'].delete()
            return
        recipients = []
        ticket = kwargs['comment'].content_object
        if 'request' in kwargs:
            username = kwargs['request'].user.first_name + " " + kwargs['request'].user.last_name
            if username == " ":
                username = kwargs['request'].user.username
        else:
            username = "Someone"
        for user in ticket.authorized_users.all():
            recipients.append(user.email)
        if ticket.assigned_to is not None:
            recipients.append(ticket.assigned_to.email)
        while kwargs['request'].user.email in recipients:
            recipients.remove(kwargs['request'].user.email)
        message = EmailMessage(username + " has commented on your ticket", \
            "<html><body>Ticket: <a href='" + \
            kwargs['request'].build_absolute_uri(
            reverse('tickets.views.show_ticket', kwargs={'ticket_id': ticket.id})) + \
            "'>" + ticket.title + "</a><br>" + \
            "Message: " + kwargs['comment'].comment + "<br>" +\
            "</body></html>", \
            settings.SERVER_EMAIL, recipients)
        message.content_subtype = "html"
        message.send()

def save_last_modified(sender, **kwargs):
    if sender == LogEntry and kwargs['instance'].get_edited_object().__class__ == Ticket:
        ticket = kwargs['instance'].get_edited_object()
        user = kwargs['instance'].user.get_full_name()
        ticket.last_modified_by = user
        ticket.save()

comment_was_posted.connect(notify_users)
post_save.connect(save_last_modified)