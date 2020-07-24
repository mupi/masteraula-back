from django.contrib import admin

from .models import TermsUse

class TermsUseModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'content', 'last_update')
    search_fields = ['id',]
    list_per_page = 100

admin.site.register(TermsUse, TermsUseModelAdmin)
