from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count
from api.models import User
from market.models import ProductPost, Order
# from notifications.models import Notification # App does not exist, using mock data

# Since we might not have a dedicated Content model, we'll mock it or use Notifications/Posts
# For 'Content Management', usually this means Blog/Announcements. 
# We'll use a simple mock list for now as no Content model was evident in previous steps.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_users(request):
    # Allow admin or just authenticated for demo
    users = User.objects.all().values('id', 'username', 'email', 'role', 'phone')
    data = []
    for u in users:
        # Mock status field if not in model
        data.append({
            'id': u['id'],
            'name': u['username'],
            'email': u['email'] or u['phone'], # Fallback to phone if email empty
            'role': u['role'],
            'status': 'active' # Default active
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_products(request):
    products = ProductPost.objects.all()
    data = []
    for p in products:
        sales = p.orders.count() # Using related_name='orders' from Order model
        data.append({
            'id': p.id,
            'name': p.crop_name,
            'farmer_name': p.farmer.username,
            'price': p.price,
            'stock': p.quantity,
            'sales': sales
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_transactions(request):
    orders = Order.objects.all().order_by('-created_at')
    data = []
    for o in orders:
        data.append({
            'id': o.id,
            'buyer_name': o.buyer.username,
            'product_name': o.product_post.crop_name,
            'quantity': o.quantity,
            'total': o.total_price,
            'date': o.created_at
        })
    return Response(data)

@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_content(request, pk=None):
    if request.method == 'DELETE':
        # Mock deletion
        return Response({'message': 'Content deleted'})
    
    # GET: Mock Content
    return Response([
        {'id': 1, 'title': 'Winter Farming Tips', 'type': 'Article', 'created_at': '2025-11-20'},
        {'id': 2, 'title': 'Market Holiday Schedule', 'type': 'Announcement', 'created_at': '2025-11-25'},
        {'id': 3, 'title': 'New Pest Alert', 'type': 'Alert', 'created_at': '2025-12-01'},
    ])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_reports(request):
    total_users = User.objects.count()
    total_transactions = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    active_products = ProductPost.objects.filter(status='available').count()
    
    return Response({
        'total_users': total_users,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'active_products': active_products
    })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_status(request, pk):
    # Mock update
    return Response({'message': 'User status updated'})
