"""
Custom storage backends for AWS S3
Separates static and media files into different directories on S3
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """Storage backend for static files on S3"""
    location = "static"
    default_acl = "public-read"
    file_overwrite = True


class MediaStorage(S3Boto3Storage):
    """Storage backend for media files on S3"""
    location = "media"
    default_acl = None
    file_overwrite = False
