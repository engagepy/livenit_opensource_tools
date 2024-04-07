from django.contrib import admin

from sites_groups.models import SitesGroup


class SitesGroupAdmin(admin.ModelAdmin):
    list_display = ('title', '_sites')

    def _sites(self, obj):
        return ', '.join([o.name for o in obj.sites.all()])


admin.site.register(SitesGroup, SitesGroupAdmin)
