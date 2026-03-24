import json
import razorpay
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Payment


@csrf_exempt
@transaction.atomic
def razorpay_webhook(request):

    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    body = request.body.decode("utf-8")
    signature = request.headers.get("X-Razorpay-Signature")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_webhook_signature(body, signature, webhook_secret)

        data = json.loads(body)
        event = data.get("event")

        razorpay_order_id = data["payload"]["payment"]["entity"]["order_id"]
        payment = Payment.objects.select_related("order").select_for_update().get(
            razorpay_order_id=razorpay_order_id
        )

        # 🔁 Prevent duplicate processing
        if payment.status == "SUCCESS":
            return HttpResponse(status=200)

        if event == "payment.captured":
            payment.status = "SUCCESS"
            payment.save(update_fields=["status"])

            order = payment.order
            order.status = "ORDER_PLACED"
            order.save(update_fields=["status"])

            for item in order.items.select_related("product"):
                product = item.product

                if product.stock < item.quantity:
                    raise Exception("Stock inconsistency")

                product.stock -= item.quantity
                product.save(update_fields=["stock"])

        elif event == "payment.failed":
            payment.status = "FAILED"
            payment.save(update_fields=["status"])

        return HttpResponse(status=200)

    except Exception as e:
        return HttpResponse(status=400)
