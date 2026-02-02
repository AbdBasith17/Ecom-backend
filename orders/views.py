from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from rest_framework import generics, permissions
from .models import Order 
from .serializers import OrderSerializer 

# Import your models
from cart.models import CartItem
from addresses.models import Address
from .models import Order, OrderItem
from payments.models import Payment
from payments.models import Payment, RevenueLog 
from products.models import Product
import razorpay
from django.conf import settings



class PlaceOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        address_id = request.data.get("address_id")
        payment_method = request.data.get("payment_method")

        cart_items = CartItem.objects.filter(cart__user=user)
        if not cart_items.exists():
            return Response({"error": "Cart empty"}, status=400)

        address = Address.objects.get(id=address_id, user=user)
        total_amount = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            user=user,
            address=address,
            total_amount=total_amount,
            payment_method=payment_method,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        payment = Payment.objects.create(order=order, amount=total_amount)

        if payment_method == "RAZORPAY":
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                "amount": int(total_amount * 100),
                "currency": "INR",
                "payment_capture": "1"
            })
            payment.razorpay_order_id = razorpay_order["id"]
            payment.save()

            # 🔥 FIX: Do NOT delete cart_items here. 
            # If we delete now, the frontend thinks the cart is empty before payment opens.
            
            return Response({
                "order_id": order.id,
                "razorpay_order_id": razorpay_order["id"],
                "amount": total_amount,
                "key": settings.RAZORPAY_KEY_ID
            })

        # COD flow - delete cart immediately
        cart_items.delete()
        return Response({"message": "Order placed (COD)"})

class CancelOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Change 'post' to 'patch' to match your frontend request
    @transaction.atomic
    def patch(self, request, pk): 
        try:
            # We use select_for_update to lock the row while we change status and stock
            order = Order.objects.select_for_update().get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if not order.can_cancel():
            return Response(
                {"error": "Order cannot be cancelled at this stage"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Reverse Stock (Crucial for inventory accuracy)
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        # 2. Financial Reversal (Only if it was an online payment)
        if order.payment_method == "RAZORPAY":
            RevenueLog.objects.create(
                order=order,
                amount=order.total_amount,
                transaction_type='EXPENSE',
                note=f"Refund/Reversal for cancelled order #{order.id}"
            )

        # 3. Update Status
        order.status = "CANCELLED"
        order.save()

        return Response({"message": "Order cancelled successfully and stock returned"})


class CheckoutSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # 🛒 1. Filter items correctlyyy
            cart_items = CartItem.objects.filter(cart__user=request.user)

            if not cart_items.exists():
                return Response({
                    "items_total": "0.00",
                    "tax": "0.00",
                    "delivery_fee": "0.00",
                    "grand_total": "0.00"
                })

            # 💰 2. Calculate Total
            items_total = sum((item.product.price * item.quantity for item in cart_items), Decimal('0.00'))

            # 🧾 3. Calculate Tax and Fees
            tax = (items_total * Decimal('0.05')).quantize(Decimal('0.01'))
            delivery_fee = Decimal('50.00') if items_total < Decimal('1000.00') else Decimal('0.00')
            grand_total = items_total + tax + delivery_fee

            return Response({
                "items_total": items_total,
                "tax": tax,
                "delivery_fee": delivery_fee,
                "grand_total": grand_total
            })

        except Exception as e:
            print(f"Checkout Summary Error: {str(e)}")
            return Response({"error": "Calculation error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class UserOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    



class AdminOrderListAPIView(generics.ListAPIView):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminUpdateOrderStatusAPIView(APIView):
    @transaction.atomic
    def patch(self, request, pk):
        try:
            # Lock the row for processing
            order = Order.objects.select_for_update().get(pk=pk)
            new_status = request.data.get("status")

            # 🛑 1. LOCKING MECHANISM
            # If the order is already Delivered, don't allow any more changes
            if order.status == "DELIVERED":
                return Response(
                    {"error": "This order is already delivered and cannot be changed."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # If the order is already Cancelled, you probably shouldn't be able to change it either
            if order.status == "CANCELLED":
                return Response(
                    {"error": "Cancelled orders cannot be modified."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. VALIDATE STATUS
            if new_status in dict(Order.STATUS_CHOICES):
                old_status = order.status
                order.status = new_status
                order.save()

                # 💰 3. REVENUE LOGIC FOR COD
                # Only log revenue if it's shifting TO delivered for the first time
                if new_status == "DELIVERED":
                    if order.payment_method == "COD":
                        RevenueLog.objects.create(
                            order=order,
                            amount=order.total_amount,
                            transaction_type='INCOME',
                            note=f"COD Order #{order.id} marked as Delivered."
                        )
                    # Note: Razorpay is already logged at payment verification
                
                return Response({"message": f"Status updated to {new_status}"})
            
            return Response({"error": "Invalid status choice"}, status=400)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

