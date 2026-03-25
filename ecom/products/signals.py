from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ProductImage

@receiver(post_delete, sender=ProductImage)
def delete_image_from_s3(sender, instance, **kwargs):
    """
    Deletes the file from the cloud storage 
    immediately after the database record is removed.
    """
    if instance.image:
        # save=False avoids a recursive save loop
        instance.image.delete(save=False)