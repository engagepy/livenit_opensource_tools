from django.contrib import admin
from django.utils.translation import ugettext as _

from jmbo.admin import ModelBaseAdmin

from superhero.forms import ImportForm
from superhero.models import Superhero


class SuperheroAdmin(ModelBaseAdmin):
    form = ImportForm

    def get_fieldsets(self, request, obj=None):
        result = super(SuperheroAdmin, self).get_fieldsets(request, obj=obj)
        result += [_("Import"), {"fields": ("files", )}],
        result = list(result)
        return (result[0], result[2], result[3], result[7])


admin.site.register(Superhero, SuperheroAdmin)
