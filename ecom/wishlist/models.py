from django.db import models
from django.conf import settings
from django.db import models 
from products.models import Product


class Wishlist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )

    def __str__(self):
        return f"{self.user.email} wishlist"
    

class WishlistItems(models.Model):
    wishlist = models.ForeignKey(
        Wishlist,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist','product')

    def __str__(self):
        return self.product.name        