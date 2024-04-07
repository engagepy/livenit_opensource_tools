from django.utils.translation import ugettext as _
from django.db import models

from jmbo.models import ModelBase


class Superhero(ModelBase):
    name = models.CharField(max_length=256, editable=False)

    class Meta:
        verbose_name_plural = _("Superheroes")
