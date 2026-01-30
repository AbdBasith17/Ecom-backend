import razorpay
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializers import PaymentVerifySerializer
from orders.models import Order


class CreateRazorpayOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")

        order = Order.objects.get(id=order_id, user=request.user)

        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={"amount": order.total_price}
        )

        if payment.razorpay_order_id:
            return Response({
                "razorpay_order_id": payment.razorpay_order_id,
                "amount": int(payment.amount * 100),
                "key": settings.RAZORPAY_KEY_ID
            })

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        razorpay_order = client.order.create({
            "amount": int(order.total_price * 100),
            "currency": "INR",
            "payment_capture": 1
        })

        payment.razorpay_order_id = razorpay_order["id"]
        payment.save(update_fields=["razorpay_order_id"])

        return Response({
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "key": settings.RAZORPAY_KEY_ID
        })



class VerifyPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment = Payment.objects.select_related("order").select_for_update().get(
            razorpay_order_id=data["razorpay_order_id"]
        )

        # 🔁 Prevent double processing
        if payment.status == "SUCCESS":
            return Response({"message": "Payment already processed"})

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            client.utility.verify_payment_signature(data)

            payment.status = "SUCCESS"
            payment.razorpay_payment_id = data["razorpay_payment_id"]
            payment.save(update_fields=["status", "razorpay_payment_id"])

            order = payment.order
            order.status = "ORDER_PLACED"
            order.save(update_fields=["status"])

            # 🔻 Reduce stock
            for item in order.items.select_related("product"):
                product = item.product

                if product.stock < item.quantity:
                    raise Exception("Insufficient stock")

                product.stock -= item.quantity
                product.save(update_fields=["stock"])

            return Response({"message": "Payment verified & order placed"})

        except razorpay.errors.SignatureVerificationError:
            payment.status = "FAILED"
            payment.save(update_fields=["status"])
            return Response({"error": "Verification failed"}, status=400)


# class VerifyPaymentAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = PaymentVerifySerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         payment = Payment.objects.get(
#             razorpay_order_id=serializer.validated_data["razorpay_order_id"]
#         )

#         payment.razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
#         payment.save(update_fields=["razorpay_payment_id"])

#         return Response({"message": "Verification recorded, waiting webhook"})
