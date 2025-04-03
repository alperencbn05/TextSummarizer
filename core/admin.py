from django.contrib import admin
from .models import Summary, GuestUsage

# Register your models here.

@admin.register(GuestUsage)
class GuestUsageAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('ip_address',)
    ordering = ('-timestamp',)
