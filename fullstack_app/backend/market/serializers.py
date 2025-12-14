from rest_framework import serializers
from .models import ProductPost, MarketPrice, Order

class ProductPostSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)
    farmer_phone = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()

    def get_buyer_name(self, obj):
        return obj.buyer.username if obj.buyer else None

    def get_farmer_phone(self, obj):
        return obj.farmer.phone if obj.farmer.phone else None

    rating = serializers.SerializerMethodField()
    sales_count = serializers.SerializerMethodField()

    def get_rating(self, obj):
        import random
        # Mock rating for decoration: 3.5 to 5.0
        return round(random.uniform(3.5, 5.0), 1)

    def get_sales_count(self, obj):
        import random
        return random.randint(10, 200)

    class Meta:
        model = ProductPost
        fields = ['id', 'farmer', 'farmer_name', 'farmer_phone', 'crop_name', 'quantity', 'price', 'location', 'status', 'date_posted', 'buyer', 'buyer_name', 'rating', 'sales_count']
        read_only_fields = ['farmer', 'date_posted', 'buyer']



class MarketPriceSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)

    class Meta:
        model = MarketPrice
        fields = ['id', 'crop_name', 'market_name', 'district', 'price_per_kg', 'date', 'source', 'updated_by', 'updated_by_name']
        read_only_fields = ['date', 'updated_by']

class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    crop_name = serializers.CharField(source='product_post.crop_name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'buyer', 'buyer_name', 'product_post', 'crop_name', 'quantity', 'total_price', 'buyer_location', 'buyer_phone', 'status', 'created_at']
        read_only_fields = ['buyer', 'total_price', 'status', 'created_at']
