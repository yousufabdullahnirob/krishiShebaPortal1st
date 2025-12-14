
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farmer_orders(request):
    logger.info(f"Request: {request.method} {request.path}")
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    # Get orders for products posted by this farmer
    orders = Order.objects.filter(product_post__farmer=request.user).order_by('-created_at')
    
    data = []
    for order in orders:
        data.append({
            'id': order.id,
            'buyer_name': order.buyer.username,
            'buyer_phone': order.buyer_phone,
            'buyer_location': order.buyer_location,
            'product_name': order.product_post.crop_name,
            'quantity': order.quantity,
            'total_price': float(order.total_price),
            'status': order.status,
            'created_at': order.created_at
        })
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    logger.info(f"Request: {request.method} {request.path}")
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can update order status'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = Order.objects.get(id=order_id, product_post__farmer=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found or you are not authorized'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    if new_status not in ['confirmed', 'rejected', 'pending']:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    order.status = new_status
    order.save()
    
    # Notify buyer about status change
    Notification.objects.create(
        user=order.buyer,
        title=f'অর্ডারের স্ট্যাটাস আপডেট: {new_status}',
        message=f"আপনার {order.product_post.crop_name} এর অর্ডারটি {new_status} করা হয়েছে।",
        notification_type='system_reminder',
        priority='medium'
    )

    return Response({'message': f'Order status updated to {new_status}'})
