import logging
import requests
import openai
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import ProductPost, MarketPrice, Order
from .serializers import ProductPostSerializer, MarketPriceSerializer, OrderSerializer
from api.models import User

logger = logging.getLogger(__name__)

class CreatePostView(generics.CreateAPIView):
    serializer_class = ProductPostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        logger.info(f"Request: {self.request.method} {self.request.path}")
        user = self.request.user
        # Allow admins and farmers
        if user.role not in ['farmer', 'admin']:
            raise serializers.ValidationError('Only farmers can create product posts')
        
        serializer.save(farmer=user)

class ViewPostsView(generics.ListAPIView):
    serializer_class = ProductPostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info(f"Request: {self.request.method} {self.request.path}")
        return ProductPost.objects.filter(status='available').order_by('-date_posted')

class BuyProductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        logger.info(f"Request: {request.method} {request.path}")
        user = request.user
        
        post = get_object_or_404(ProductPost, pk=pk, status='available')
        if user == post.farmer:
            return Response({"error": "Cannot buy your own product."}, status=status.HTTP_403_FORBIDDEN)
        
        # Legacy behavior: Mark as sold immediately
        post.status = 'sold'
        post.buyer = user
        post.save()
        serializer = ProductPostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CreateOrderView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        logger.info(f"Request: {self.request.method} {self.request.path}")
        user = self.request.user
        
        post_id = self.request.data.get('product_post')
        post = get_object_or_404(ProductPost, id=post_id)
        
        if post.status != 'available':
             raise serializers.ValidationError("This product is no longer available.")

        quantity = float(self.request.data.get('quantity', 0))
        if quantity <= 0:
             raise serializers.ValidationError("Quantity must be positive")
        if quantity > post.quantity:
             raise serializers.ValidationError(f"Available quantity is only {post.quantity}kg")
             
        total_price = quantity * float(post.price)
        
        serializer.save(
            buyer=user, 
            product_post=post,
            total_price=total_price
        )
        
        # If full quantity ordered, mark as sold or update quantity
        post.quantity -= quantity
        if post.quantity <= 0:
            post.quantity = 0
            post.status = 'sold'
        post.save() 
        
        # Log logic or notification could go here
        # But user expects 'Order' to mean something.
        logger.info(f"New Order created: {quantity}kg of {post.crop_name}")

class MarketPricesListView(generics.ListAPIView):
    serializer_class = MarketPriceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        logger.info(f"Request: {self.request.method} {self.request.path}")
        return MarketPrice.objects.all().order_by('-date')

class CreateMarketPriceView(generics.CreateAPIView):
    serializer_class = MarketPriceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        logger.info(f"Request: {self.request.method} {self.request.path}")
        user = self.request.user
        if user.role != 'admin':
            raise serializers.ValidationError('Only admins can create market prices')
        serializer.save(updated_by=user)

class AISuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        crop = request.GET.get('crop')
        if not crop:
            return Response({"error": "Crop parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Request: {request.method} {request.path}")
        user = request.user
        
        # Get current prices for context
        prices = MarketPrice.objects.filter(crop_name__icontains=crop).order_by('-date')[:10]
        price_context = ""
        if prices:
            avg_price = sum(float(p.price_per_kg) for p in prices) / len(prices)
            price_context = f"Current average price for {crop} is {avg_price:.2f} BDT/kg. Recent prices: {[f'{p.price_per_kg} BDT/kg on {p.date}' for p in prices[:3]]}."
        else:
            price_context = f"No recent price data for {crop}."

        # Use OpenAI API for AI suggestion
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an agricultural market expert providing price suggestions for farmers in Bangladesh. Provide concise, actionable advice based on market trends."},
                    {"role": "user", "content": f"Based on this data: {price_context} Provide a market price suggestion for {crop}."}
                ]
            )
            suggestion = response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to mock suggestion
            if prices:
                avg_price = sum(float(p.price_per_kg) for p in prices) / len(prices)
                suggestion = f"Current average price for {crop} is {avg_price:.2f} BDT/kg. Consider selling if price is above {avg_price * 1.1:.2f} BDT/kg."
            else:
                # Custom advice for specific crops
                if "soybean" in crop.lower():
                    suggestion = "Soybean prices are currently trending upwards due to high demand. Hold for a few weeks if possible for better returns (Expected > 120 BDT/kg)."
                elif "rice" in crop.lower():
                    suggestion = "Rice market is stable. Good time to sell if you have storage constraints. Current market float is around 50-70 BDT/kg."
                elif "onion" in crop.lower():
                    suggestion = "Onion prices are volatile. Check daily local market rates before selling."
                elif "potato" in crop.lower():
                    suggestion = "Potato cold storage demand is increasing. Expect price hike next month."
                elif "garlic" in crop.lower() or "রসুন" in crop.lower():
                    suggestion = "Garlic market is high. Imported garlic is stabilizing local prices. Current range: 200-250 BDT/kg."
                elif "ginger" in crop.lower() or "আদা" in crop.lower():
                    suggestion = "Ginger prices are peaking. Good time to sell if you have stock. Expect fluctuations next week."
                elif "lentil" in crop.lower() or "masur" in crop.lower() or "ডাল" in crop.lower():
                    suggestion = "Lentil demand is steady. Prices are expected to remain between 130-150 BDT/kg."
                elif "chili" in crop.lower() or "মরিচ" in crop.lower():
                    suggestion = "Green Chili prices are highly volatile and weather-dependent. Current high prices may drop if supply improves."
                elif "tomato" in crop.lower() or "টমেটো" in crop.lower():
                    suggestion = "Tomato prices are seasonal. Late winter harvest may lower prices. Sell now for better margin (~50 BDT/kg)."
                elif "wheat" in crop.lower() or "গম" in crop.lower():
                    suggestion = "Wheat market is stable globally. Local prices are fair at 40-50 BDT/kg."
                elif "corn" in crop.lower() or "maize" in crop.lower() or "ভুট্টা" in crop.lower():
                    suggestion = "Corn demand from poultry sector is strong. Prices (30-40 BDT/kg) are favorable for sellers."
                elif "eggplant" in crop.lower() or "begun" in crop.lower() or "বেগুন" in crop.lower():
                    suggestion = "Eggplant prices vary by variety and freshness. Premium quality is fetching 60-80 BDT/kg."
                elif "mustard" in crop.lower() or "সরিষা" in crop.lower():
                    suggestion = "Mustard oil and seed prices are remaining high. Good expected revenue for growers."
                else:
                    suggestion = f"No specific recent trends for {crop}. General advice: Check multiple local markets before selling to get the best deal."

        return Response({"suggestion": suggestion})

class AutoRefreshPricesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f"Request: {request.method} {request.path}")
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Only admins can refresh prices'}, status=status.HTTP_403_FORBIDDEN)

        import random
        from datetime import date

        # Realistic Base Prices for BD Market (Avg)
        base_prices = {
            'Rice (Moth Bean)': 65.0, # Approximate for fine rice
            'Wheat': 45.0,
            'Potato': 35.0,
            'Tomato': 80.0,
            'Onion': 90.0,
            'Garlic': 220.0,
            'Ginger': 180.0,
            'Lentil (Masur)': 140.0,
            'Green Chili': 120.0,
            'Eggplant (Begun)': 60.0,
            'Mustard Oil': 250.0,
            'Corn (Maize)': 35.0,
            'Soybean': 110.0
        }

        districts = [
            'Dhaka', 'Chittagong', 'Rajshahi', 'Khulna', 'Barisal', 'Sylhet', 'Rangpur', 'Mymensingh',
            'Comilla', 'Bogra', 'Jessore', 'Dinajpur', 'Pabna', 'Tangail', 'Faridpur'
        ]
        
        # Fluctuation factors (simulating supply/demand)
        market_trend = random.choice([0.95, 1.0, 1.05]) # -5%, 0%, +5% overall trend
        
        new_prices = []
        for crop, base_price in base_prices.items():
            # Apply general market trend
            trend_price = base_price * market_trend
            
            for district in districts:
                # District variance: +/- 10% random logic specific to district can be added here
                # e.g. Transport cost makes Dhaka more expensive usually
                district_factor = 1.0
                if district == 'Dhaka' or district == 'Chittagong':
                    district_factor = 1.1 # 10% more expensive in metros
                elif district in ['Dinajpur', 'Bogra', 'Rangpur']: # production hubs
                    district_factor = 0.9 # 10% cheaper
                
                # Daily random fluctuation +/- 5%
                daily_fluctuation = random.uniform(0.95, 1.05)
                
                final_price = round(trend_price * district_factor * daily_fluctuation, 2)
                
                new_prices.append({
                    "crop_name": crop,
                    "market_name": f"{district} Sadar Market",
                    "district": district,
                    "price_per_kg": final_price
                })

        created_count = 0
        # Clear old prices to keep the list fresh or just append? 
        # Usually tracking history is good, but for this demo list we might want to see latest.
        # Let's keep history but the frontend usually fetches latest. 
        # Ideally we only fetch today's data in the loop. 
        
        # Check if we already have prices for today to avoid duplicates if user refreshes multiple times
        today = date.today()
        existing_today = MarketPrice.objects.filter(date=today).exists()
        
        if not existing_today:
            for price_data in new_prices:
                MarketPrice.objects.create(
                    **price_data,
                    source='simulated_govt_data',
                    updated_by=user
                )
                created_count += 1
            return Response({"message": f"Successfully fetched and updated {created_count} market prices for {today} from National Database (Simulated)."})
        else:
            return Response({"message": f"Market prices for {today} are already up to date."})

class WelcomeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info(f"Request: {request.method} {request.path}")
        return Response({"message": "Welcome to the Market API!"})

class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        logger.info(f"Request: {request.method} {request.path}")
        user = request.user
        
        message = request.data.get('message')
        if not message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

        post = get_object_or_404(ProductPost, pk=pk)
        # Mock sending message
        logger.info(f"Message sent to seller {post.farmer.username}: {message}")

        return Response({"message": "Message sent successfully"})

class MyOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')

class MyDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        my_posts = ProductPost.objects.filter(farmer=user)
        total_stock = sum(p.quantity for p in my_posts.filter(status='available'))
        total_sold_posts = my_posts.filter(status='sold').count() 
        
        # Mock demand data
        demand = int(total_stock * 0.9) + 50
        
        return Response({
            "total_stock": total_stock,
            "demand": demand,
            "total_sold_posts": total_sold_posts
        })
