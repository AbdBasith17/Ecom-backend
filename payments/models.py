from django.db import models


class Payment(models.Model):

    STATUS_CHOICES = [
        ("INITIATED", "Initiated"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="INITIATED")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.id}"



class RevenueLog(models.Model):
    TRANSACTION_TYPES = (
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense/Refund'),
    )
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    note = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)