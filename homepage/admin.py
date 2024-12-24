from django.contrib import admin

from homepage.models import HomepageContent, HomepageSection, AdsSection

# Register your models here.

class HomepageContentAdmin(admin.ModelAdmin):
    list_display = ['title_text', 'section_code']
    search_fields = ['title_text']
    list_filter = ['section_code']

admin.site.register(HomepageSection)
admin.site.register(HomepageContent, HomepageContentAdmin)
admin.site.register(AdsSection)