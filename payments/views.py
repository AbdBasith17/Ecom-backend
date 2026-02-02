import razorpay
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Payment ,RevenueLog
from .serializers import PaymentVerifySerializer
from orders.models import Order
from cart.models import CartItem

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

        try:
            payment = Payment.objects.select_related("order").select_for_update().get(
                razorpay_order_id=data["razorpay_order_id"]
            )
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found"}, status=404)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature(data)

            # 1. Update Payment & Order
            payment.status = "SUCCESS"
            payment.razorpay_payment_id = data["razorpay_payment_id"]
            payment.save()

            order = payment.order
            order.status = "ORDER_PLACED"
            order.save()

            # 2. Record Revenue
            RevenueLog.objects.create(
                order=order,
                amount=order.total_amount,
                transaction_type='INCOME',
                note=f"Razorpay ID: {data['razorpay_payment_id']}"
            )

            # ✅ 3. CLEAR CART NOW
            CartItem.objects.filter(cart__user=request.user).delete()

            return Response({"message": "Success", "order_id": order.id}, status=200)

        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "Invalid signature"}, status=400)


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
