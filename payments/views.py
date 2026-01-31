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
        # 1. Validate incoming Razorpay data
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 2. Get payment record and lock it for update to prevent race conditions
        try:
            payment = Payment.objects.select_related("order").select_for_update().get(
                razorpay_order_id=data["razorpay_order_id"]
            )
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found"}, status=404)

        # 🔁 3. Prevent double processing
        if payment.status == "SUCCESS":
            return Response({"message": "Payment already processed"})

        # 4. Initialize Razorpay Client
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            # 5. Verify Signature
            client.utility.verify_payment_signature(data)

            # 6. Update Payment Status
            payment.status = "SUCCESS"
            payment.razorpay_payment_id = data["razorpay_payment_id"]
            payment.save(update_fields=["status", "razorpay_payment_id"])

            # 7. Update Order Status
            order = payment.order
            order.status = "ORDER_PLACED"
            order.save(update_fields=["status"])

            # 💰 8. RECORD THE REVENUE (The new Ledger step)
            # Since the payment is successful, we log the income now.
            RevenueLog.objects.create(
                order=order,
                amount=order.total_amount,
                transaction_type='INCOME',
                note=f"Razorpay payment verified. ID: {data['razorpay_payment_id']}"
            )

            # NOTE: We do NOT reduce stock here because we already 
            # reduced it in PlaceOrderAPIView to reserve the items.

            return Response({
                "message": "Payment verified, revenue logged & order placed",
                "order_id": order.id
            }, status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            # 9. Handle Verification Failure
            payment.status = "FAILED"
            payment.save(update_fields=["status"])
            
            # Note: We keep the order status as 'PENDING'. 
            # You can later have a cleanup task to return stock if not paid within X minutes.
            return Response({"error": "Verification failed"}, status=400)
            
        except Exception as e:
            # 10. Handle unexpected errors
            return Response({"error": str(e)}, status=500)


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
