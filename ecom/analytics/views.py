from django.db.models import Sum
from django.db.models.functions import TruncDate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from datetime import timedelta
from django.utils import timezone


from payments.models import RevenueLog
from orders.models import Order
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
      
        total_revenue = RevenueLog.objects.filter(
            transaction_type='INCOME'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_orders = Order.objects.count()
        total_customers = User.objects.filter(is_staff=False).count()
        total_products = Product.objects.count()

      
        thirty_days_ago = timezone.now() - timedelta(days=30)
        revenue_history = (
            RevenueLog.objects.filter(
                transaction_type='INCOME',
                created_at__gte=thirty_days_ago
            )
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(rev=Sum('amount'))
            .order_by('date')
        )

        top_products = Product.objects.filter(sold__gt=0).order_by('-sold')[:5]
        
        pie_data = [
            {"name": p.title, "value": p.sold} for p in top_products
        ]

        return Response({
            "stats": {
                "revenue": float(total_revenue),
                "orders": total_orders,
                "customers": total_customers,
                "products": total_products
            },
            "charts": {
                "revenue_history": list(revenue_history),
                "top_products": pie_data
            }
        })