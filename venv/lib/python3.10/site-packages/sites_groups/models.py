from django.db import models


class SitesGroup(models.Model):
    title = models.CharField(
        max_length=256,
        help_text='A short descriptive title.',
    )
    sites = models.ManyToManyField(
        'sites.Site',
        help_text='Sites that belong to this group.',
    )

    class Meta:
        ordering = ('title',)

    def __unicode__(self):
        return self.title

    @property
    def site_ids(self):
        return self.sites.all().values_list('id', flat=True)
