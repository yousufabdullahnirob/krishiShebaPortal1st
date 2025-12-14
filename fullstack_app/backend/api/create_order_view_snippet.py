
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    
    # Get parameters
    product_post_id = request.data.get('product_post')
    quantity = request.data.get('quantity')
    buyer_location = request.data.get('buyer_location')
    buyer_phone = request.data.get('buyer_phone')

    if not all([product_post_id, quantity, buyer_location, buyer_phone]):
        return Response({'error': 'All fields (product_post, quantity, buyer_location, buyer_phone) are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        product = ProductPost.objects.get(id=product_post_id)
    except ProductPost.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        quantity = float(quantity)
    except ValueError:
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

    if product.status != 'available':
        return Response({'error': 'Product is not available'}, status=status.HTTP_400_BAD_REQUEST)
    
    if quantity > product.quantity:
        return Response({'error': f'Available quantity is only {product.quantity} kg'}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate price
    total_price = quantity * float(product.price)

    # Create Order
    order = Order.objects.create(
        buyer=user,
        product_post=product,
        quantity=quantity,
        total_price=total_price,
        buyer_location=buyer_location,
        buyer_phone=buyer_phone,
        status='pending' 
    )

    # Update Product Quantity
    if quantity == product.quantity:
        product.status = 'sold'
        product.buyer = user
    else:
        # Partial buy - reduce quantity
        product.quantity -= quantity
        # product.status remains available
    
    product.save()

    # Create Notification for Farmer
    from api.models import Notification
    Notification.objects.create(
        user=product.farmer,
        title='নতুন অর্ডার এসেছে!',
        message=f"{user.username} আপনার {product.crop_name} এর জন্য {quantity} kg অর্ডার করেছেন।",
        notification_type='price_update',
        priority='high'
    )

    return Response({
        'message': 'Order placed successfully',
        'order_id': order.id,
        'total_price': total_price
    }, status=status.HTTP_201_CREATED)
