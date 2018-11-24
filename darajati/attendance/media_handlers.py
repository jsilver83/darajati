import os

from django.conf import settings


def upload_excuse_attachments(instance, filename):
    sub_folder = 'excuse_attachments/%s/%s/%s/%s' % (instance.excuse_type,
                                                     instance.start_date.year,
                                                     instance.start_date.month,
                                                     instance.university_id,)
    return upload_location(sub_folder, filename)


# defines where to save uploaded student documents
def upload_location(sub_folder, filename):
    ext = os.path.splitext(filename)[1]

    file_name = '%s%s' % (sub_folder, ext)
    full_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if os.path.exists(full_path):
        os.remove(full_path)
    return file_name
