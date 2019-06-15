from django.core.exceptions import ValidationError
from django.conf import settings
from darajati.utils import size_format
from django.utils.translation import ugettext_lazy as _


"""
 ABOUT: this file is supposed to hold validators that are shared across apps
"""


# validates file extensions for uploaded documents
def validate_file_extension(value):
    import os

    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.bmp', '.gif', '.png', '.jpg', '.jpeg']
    if ext not in valid_extensions:
        raise ValidationError(
            _('File extension (%(ext)s) not allowed!'),
            params={'ext': ext},
            code='ext_not_allowed',
        )

    if value.size > settings.MAX_FILE_UPLOAD_SIZE:
        raise ValidationError(
            _('File size {} is larger than {}!'.format(size_format(value.size),
                                                       size_format(settings.MAX_FILE_UPLOAD_SIZE))),
            code='size_not_allowed',
        )
