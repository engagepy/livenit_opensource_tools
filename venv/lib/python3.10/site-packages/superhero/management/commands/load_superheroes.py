import os
import zipfile
from StringIO import StringIO
import shutil
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.sites.models import Site
from django.conf import settings

from superhero.models import Superhero


class Command(BaseCommand):
    """Adapted from forms.ImportForm"""

    help = "Scan directory for ZIP files and load them as superhero objects."

    option_list = BaseCommand.option_list + (
        make_option('--directory', dest='directory', action='store',
            default='',
            help="Directory containing ZIP files."
        ),
    )

    @transaction.commit_on_success
    def handle(self, *args, **options):
        root = options["directory"]

        for count, filename in enumerate(os.listdir(root)):
            if not filename.lower().endswith(".zip"): continue

            item = open(os.path.join(root, filename), "rb")

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
                    # Skip if index.html not in top level of archive
                    if not [n for n in zfp.namelist() if "index.html" in n]:
                        continue

                    # Ensure superhero directory exists
                    dir = os.path.join(settings.MEDIA_ROOT, "superhero")
                    if not os.path.exists(dir):
                        os.mkdir(dir)

                    name = ".".join(filename.split(".")[:-1])
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
