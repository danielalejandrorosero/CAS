from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import CitacionComite, ArchivoAdjuntoCitacion, SeguimientoCitacion

admin.site.register(CitacionComite)
admin.site.register(ArchivoAdjuntoCitacion)
admin.site.register(SeguimientoCitacion)