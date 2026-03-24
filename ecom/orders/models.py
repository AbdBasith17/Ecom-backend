from django.db import models
from django.conf import settings


class Order(models.Model):

    STATUS_CHOICES = [
        ("ORDER_PLACED", "Order Placed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_METHODS = [
        ("COD", "Cash On Delivery"),
        ("RAZORPAY", "Razorpay"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey("addresses.Address", on_delete=models.SET_NULL, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="ORDER_PLACED")
    created_at = models.DateTimeField(auto_now_add=True)

    def can_cancel(self):
        return self.status in ["ORDER_PLACED", "SHIPPED"]

    def __str__(self):
        return f"Order {self.id} - {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product} x {self.quantity}"
