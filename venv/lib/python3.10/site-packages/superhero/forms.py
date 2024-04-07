import os
import zipfile
from StringIO import StringIO
import shutil

from django import forms
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.conf import settings

from superhero.fields import FileMultiField
from superhero.models import Superhero


class ImportForm(forms.ModelForm):
    files = FileMultiField(
        required=True,
        label=_("Zip file(s)"),
        help_text=_(
            """One or more zip files containing HTML, CSS, Javascript and
            images. The top level of the zip file must contain an index.html
            else it is omitted."""
        )
    )

    class Meta:
        model = Superhero

    def save(self, *args, **kwargs):
        initial_obj = super(ImportForm, self).save(*args, **kwargs)
        if self.cleaned_data["files"]:
            for count, item in enumerate(self.cleaned_data["files"]):
                item.seek(0)

                # Zip file?
                itemfp = StringIO(item.read())
                item.seek(0)
                try:
                    zfp = zipfile.ZipFile(itemfp, "r")
                except:
                    # zipfile does not raise a specific exception
                    continue
                else:
                    if not zfp.testzip():
                        print zfp.namelist()
                        # Skip if index.html not in top level of archive
                        if not [n for n in zfp.namelist() if "index.html" in n]:
                            continue

                        # Ensure superhero directory exists
                        dir = os.path.join(settings.MEDIA_ROOT, "superhero")
                        if not os.path.exists(dir):
                            os.mkdir(dir)

                        name = ".".join(item.name.split(".")[:-1])
                        target = os.path.join(dir, name)

                        # Remove target if it exists because it may contain
                        # stale files
                        if os.path.exists(target):
                            shutil.rmtree(target)

                        zfp.extractall(path=target)

                        # Create or update object utilising the initial obj
                        # first
                        if not count:
                            initial_obj.title = name.capitalize()
                            initial_obj.name = name
                        else:
                            try:
                                obj = Superhero.objects.get(name=name)
                            except Superhero.DoesNotExist:
                                obj = Superhero.objects.create(
                                    title=name.capitalize(), name=name
                                )
                                obj.sites = Site.objects.all()
                                obj.save()

        return super(ImportForm, self).save(*args, **kwargs)
