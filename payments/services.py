import razorpay
from django.conf import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(payment):
    razorpay_order = client.order.create({
        "amount": int(payment.amount * 100),
        "currency": "INR",
        "payment_capture": "1"
    })

    payment.razorpay_order_id = razorpay_order["id"]
    payment.save()

    return razorpay_order
