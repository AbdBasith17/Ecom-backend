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


class VerifyPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payment = Payment.objects.select_related("order").get(
                razorpay_order_id=data["razorpay_order_id"]
            )
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=404)

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            client.utility.verify_payment_signature(data)

            payment.status = "SUCCESS"
            payment.razorpay_payment_id = data["razorpay_payment_id"]
            payment.save()

            order = payment.order
            order.status = "SHIPPED"
            order.save()

            # Reduce stock
            for item in order.items.all():
                product = item.product
                product.stock -= item.quantity
                product.save()

            return Response({"message": "Payment verified successfully"})

        except razorpay.errors.SignatureVerificationError:
            payment.status = "FAILED"
            payment.save()
            return Response({"error": "Verification failed"}, status=400)




class CreateRazorpayOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({"error": "Order ID required"}, status=400)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={"amount": order.total_price}
        )

        if payment.razorpay_order_id:
            return Response({
                "razorpay_order_id": payment.razorpay_order_id,
                "amount": int(payment.amount * 100),
                "key": settings.RAZORPAY_KEY_ID
            })

        
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        razorpay_order = client.order.create({
            "amount": int(order.total_price * 100),
            "currency": "INR",
            "payment_capture": "1"
        })

        payment.razorpay_order_id = razorpay_order["id"]
        payment.save()

        return Response({
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "key": settings.RAZORPAY_KEY_ID
        })

