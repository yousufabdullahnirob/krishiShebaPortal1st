import logging
import requests
from django.shortcuts import render, get_object_or_404

logger = logging.getLogger(__name__)
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import User, Post, Comment, Problem, Reply, Crop, ChatMessage, WeatherData, Activity, Timeline, Progress, MarketPrice, ExpenseCalculation, Notification, ProblemSolution, CropRecommendation, KnowledgeBase
from market.models import ProductPost, Order
from django.db.models import Q
from .serializers import UserSerializer, PostSerializer, CommentSerializer, ProblemSerializer, ReplySerializer, CropSerializer, ChatMessageSerializer, WeatherDataSerializer, ActivitySerializer, TimelineSerializer, ProgressSerializer, MarketPriceSerializer, ExpenseCalculationSerializer, NotificationSerializer, CropRecommendationSerializer

from django.contrib.auth import authenticate 
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q

from django.core.mail import send_mail
from .models import OTPVerification
import random

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    logger.info(f"Request: {request.method} {request.path}")
    logger.info(f"Request Data: {request.data}") # Debug logging
    identifier = request.data.get('identifier', '').strip().lower()
    role = request.data.get('role', 'buyer').strip().lower()
    purpose = request.data.get('purpose', 'registration') # 'registration' or 'reset'

    if not identifier:
        return Response({'error': 'Identifier (Phone/Email) is required'}, status=status.HTTP_400_BAD_REQUEST)

    user_exists = User.objects.filter(Q(username=identifier) | Q(phone=identifier) | Q(email=identifier)).exists()

    if purpose == 'registration':
         # Check if user already exists
        if user_exists:
            return Response({'error': 'User with this identifier already exists. Please login.'}, status=status.HTTP_400_BAD_REQUEST)
    elif purpose == 'reset':
        # Check if user exists for password reset
        if not user_exists:
            return Response({'error': 'User with this identifier does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    # Generate OTP
    otp_code = str(random.randint(100000, 999999))
    
    # Save OTP
    OTPVerification.objects.create(identifier=identifier, otp_code=otp_code)

    # Send OTP
    try:
        if '@' in identifier:
            # Send Email
            send_mail(
                'Agroby OTP Code',
                f'Your OTP for {purpose} is: {otp_code}',
                settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@agroby.com',
                [identifier],
                fail_silently=False,
            )
            message = "OTP sent to email"
        else:
            # Send SMS (Mocking for now)
            # In a real app, you would call: sms_gateway.send(identifier, otp_code)
            logger.info(f"SMS OTP for {identifier}: {otp_code}")
            print(f"\n\n>>> REAL SMS WOULD BE SENT TO {identifier}: {otp_code} <<<\n\n")
            message = f"OTP sent to phone: {otp_code} (Dev Mode)"
    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        return Response({'error': f'Failed to send OTP: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'message': message, 'otp_debug': otp_code})

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    logger.info(f"Request: {request.method} {request.path}")
    identifier = request.data.get('identifier', '').strip().lower()
    otp_code = request.data.get('otp', '').strip()
    new_password = request.data.get('new_password', '').strip()

    if not identifier or not otp_code or not new_password:
        return Response({'error': 'Identifier, OTP and New Password are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify OTP
    try:
        verification = OTPVerification.objects.filter(identifier=identifier, otp_code=otp_code, is_verified=False).latest('created_at')
        if verification.is_expired():
            return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as verified
        verification.is_verified = True
        verification.save()
        
        # Find user and reset password
        user = User.objects.filter(Q(username=identifier) | Q(phone=identifier) | Q(email=identifier)).first()
        if not user:
             return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successful. Please login.'})
        
    except OTPVerification.DoesNotExist:
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    logger.info(f"Request: {request.method} {request.path}")
    identifier = request.data.get('identifier', '').strip().lower()
    otp_code = request.data.get('otp', '').strip()

    if not identifier or not otp_code:
        return Response({'error': 'Identifier and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify OTP
    try:
        verification = OTPVerification.objects.filter(identifier=identifier, otp_code=otp_code, is_verified=False).latest('created_at')
        if verification.is_expired():
            return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        verification.is_verified = True
        verification.save()
        return Response({'message': 'OTP verified successfully'})
        
    except OTPVerification.DoesNotExist:
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    logger.info(f"Request: {request.method} {request.path}")
    identifier = request.data.get('identifier', '').strip().lower()
    password = request.data.get('password', '').strip()
    role = request.data.get('role', 'farmer').strip().lower()
    name = request.data.get('name', '').strip()

    if not identifier or not password:
        return Response({'error': 'Identifier (Phone/Email) and Password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if role not in ['farmer', 'buyer', 'expert', 'admin']:
        return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

    # Enforce OTP verification for non-farmers
    if role != 'farmer':
        try:
             # Check if there is a verified OTP for this identifier in the last 15 minutes
            verification = OTPVerification.objects.filter(identifier=identifier, is_verified=True).latest('created_at')
            if verification.is_expired(): # Reuse expiry logic or add separate verified expiry? assuming 10 mins valid to register
                 return Response({'error': 'OTP verification expired. Please verify again.'}, status=status.HTTP_400_BAD_REQUEST)
        except OTPVerification.DoesNotExist:
            return Response({'error': 'Please verify OTP first.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if User.objects.filter(Q(username=identifier) | Q(phone=identifier) | Q(email=identifier)).exists():
        return Response({'error': 'User with this identifier already exists'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Create user
        user = User.objects.create_user(
            username=identifier,
            password=password,
            role=role,
            first_name=name
        )
        
        # Set phone or email based on format
        if '@' in identifier:
            user.email = identifier
        elif identifier.isdigit():
            user.phone = identifier
        user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return Response({'error': f'Registration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    logger.info(f"Request: {request.method} {request.path}")
    identifier = request.data.get('identifier', '').strip().lower()
    password = request.data.get('password', '').strip()
    
    if not identifier or not password:
        return Response({'error': 'Identifier and Password are required'}, status=status.HTTP_400_BAD_REQUEST)

    user = None
    # Try to find user by username, phone, or email
    try:
        user = User.objects.get(Q(username=identifier) | Q(phone=identifier) | Q(email=identifier))
    except User.DoesNotExist:
        # For security, don't reveal that user doesn't exist
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
    # Check password
    if not user.check_password(password):
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({'error': 'Account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserSerializer(user).data,
        'token': str(refresh.access_token),
        'refresh': str(refresh)
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def posts_list(request):
    logger.info(f"Request: {request.method} {request.path}")
    posts = Post.objects.all().order_by('-created_at')[:50]
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET', 'OPTIONS'])
def search_posts(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Simple auth check for demo
    # Auth handled by DEFAULT_PERMISSION_CLASSES


    query = request.GET.get('q', '').strip()
    if query:
        posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).order_by('-created_at')[:50]
    else:
        posts = Post.objects.none()  # Return no posts if no query
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def create_post(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Simple auth check for demo
    user = request.user


    if user.role != 'admin':
        return Response({'error': 'Only admins can create posts'}, status=status.HTTP_403_FORBIDDEN)

    serializer = PostSerializer(data=request.data, files=request.FILES)
    if serializer.is_valid():
        serializer.save(author=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_comment(request, post_id):
    logger.info(f"Request: {request.method} {request.path}")
    # Simple auth check for demo
    user = request.user


    post = get_object_or_404(Post, id=post_id)
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(post=post, author=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'OPTIONS'])
def problems_list(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Simple auth check for demo
    user = request.user
    if user.role == 'admin':
        problems = Problem.objects.all().order_by('-created_at')
    else:
        problems = Problem.objects.all().order_by('-created_at') if user.role == 'farmer' else Problem.objects.all().order_by('-created_at')


    serializer = ProblemSerializer(problems, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def create_problem(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Simple auth check for demo
    user = request.user
    if user.role != 'farmer':
        return Response({'error': 'Only farmers can create problems'}, status=status.HTTP_403_FORBIDDEN)


    serializer = ProblemSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(farmer=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_reply(request, problem_id):
    logger.info(f"Request: {request.method} {request.path}")
    # Simple auth check for demo
    user = request.user
    if user.role != 'admin':
        return Response({'error': 'Only admins can reply'}, status=status.HTTP_403_FORBIDDEN)


    problem = get_object_or_404(Problem, id=problem_id)
    serializer = ReplySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(problem=problem, admin=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'OPTIONS'])
def stats(request):
    logger.info(f"Request: {request.method} {request.path}")
    farmers_count = User.objects.filter(role='farmer').count()
    problems_count = Problem.objects.count()
    posts_count = Post.objects.count()
    return Response({
        'farmers': farmers_count,
        'problems': problems_count,
        'posts': posts_count
    })

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
@authentication_classes([])
def crops_list(request):
    logger.info(f"Request: {request.method} {request.path}")
    crops = Crop.objects.all()
    serializer = CropSerializer(crops, many=True)
    return Response(serializer.data)

@api_view(['GET', 'OPTIONS'])
def crop_description(request, crop_id):
    logger.info(f"Request: {request.method} {request.path}")
    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    # Generate general description and care instructions
    description = generate_crop_description(crop.name, crop.season)

    return Response({
        'crop': crop.name,
        'season': crop.season,
        'description': description
    })

def generate_crop_description(crop_name, season):
    descriptions = {
        'Lentil (Masoor)': {
            'description': 'মসুর ডাল একটি প্রোটিন সমৃদ্ধ শীতকালীন ফসল। এটি মাটির উর্বরতা বাড়ায় এবং অন্যান্য ফসলের জন্য ভালো।',
            'care': 'শীতকালে বপন করুন। মাটি ভালোভাবে প্রস্তুত করুন। নিয়মিত সেচ দিন কিন্তু অতিরিক্ত পানি এড়িয়ে চলুন।'
        },
        'Chickpea (Chana)': {
            'description': 'ছোলা একটি শক্তিশালী শীতকালীন ফসল যা প্রোটিন এবং খনিজ সমৃদ্ধ। এটি মাটির নাইট্রোজেন বাড়ায়।',
            'care': 'শীতকালে বপন করুন। মাটি ভালোভাবে নিষ্কাশন করুন। ফুল ধরার সময় সেচ কমিয়ে দিন।'
        },
        'Mung Bean': {
            'description': 'মুগ ডাল একটি দ্রুত বর্ধনশীল গ্রীষ্মকালীন ফসল। এটি প্রোটিন এবং ভিটামিন সমৃদ্ধ।',
            'care': 'গ্রীষ্মকালে বপন করুন। উষ্ণ আবহাওয়া প্রয়োজন। নিয়মিত সেচ দিন এবং ছত্রাক রোগ থেকে রক্ষা করুন।'
        },
        'Black Gram (Urad)': {
            'description': 'উরদ ডাল একটি প্রোটিন সমৃদ্ধ গ্রীষ্মকালীন ফসল। এটি ভারতীয় রন্ধনশৈলীতে গুরুত্বপূর্ণ।',
            'care': 'গ্রীষ্মকালে বপন করুন। ভালো নিষ্কাশনযুক্ত মাটি প্রয়োজন। ফুল ধরার সময় সেচ বাড়ান।'
        },
        'Pigeon Pea (Arhar)': {
            'description': 'আরহর ডাল একটি দীর্ঘমেয়াদী গ্রীষ্মকালীন ফসল। এটি মাটির উর্বরতা বাড়ায়।',
            'care': 'গ্রীষ্মকালে বপন করুন। খরা সহনশীল। নিয়মিত পরিচর্যা করুন এবং পোকামাকড় থেকে রক্ষা করুন।'
        },
        'Cowpea (Barbati)': {
            'description': 'বারবাটি একটি বহুমুখী গ্রীষ্মকালীন ফসল। এটি খরা সহনশীল এবং প্রোটিন সমৃদ্ধ।',
            'care': 'গ্রীষ্মকালে বপন করুন। কম পানিতে বেঁচে থাকে। নাইট্রোজেন সার ব্যবহার করুন।'
        },
        'Horse Gram': {
            'description': 'কুলথি একটি শক্তিশালী শীতকালীন ফসল। এটি খরা এবং দরিদ্র মাটিতে ভালো জন্মে।',
            'care': 'শীতকালে বপন করুন। কম সেচ প্রয়োজন। প্রাকৃতিকভাবে রোগ প্রতিরোধী।'
        },
        'Field Pea': {
            'description': 'মটরশুটি একটি শীতকালীন ফসল যা প্রোটিন এবং ফাইবার সমৃদ্ধ।',
            'care': 'শীতকালে বপন করুন। ঠান্ডা আবহাওয়া ভালো। নিয়মিত সেচ দিন।'
        },
        'Kidney Bean (Rajma)': {
            'description': 'রাজমা একটি প্রোটিন সমৃদ্ধ শীতকালীন ফসল। এটি ভারতীয় খাবারে জনপ্রিয়।',
            'care': 'শীতকালে বপন করুন। ভালো নিষ্কাশনযুক্ত মাটি প্রয়োজন। ফুল ধরার সময় সেচ বাড়ান।'
        },
        'Broad Bean (Sem)': {
            'description': 'শিম একটি প্রোটিন সমৃদ্ধ শীতকালীন ফসল। এটি ঠান্ডা আবহাওয়ায় ভালো জন্মে।',
            'care': 'শীতকালে বপন করুন। ঠান্ডা আবহাওয়া প্রয়োজন। নিয়মিত সেচ দিন।'
        },
        'Moth Bean': {
            'description': 'মথ ডাল একটি খরা সহনশীল গ্রীষ্মকালীন ফসল। এটি রাজস্থানী খাবারে জনপ্রিয়।',
            'care': 'গ্রীষ্মকালে বপন করুন। খুব কম পানিতে বেঁচে থাকে। প্রাকৃতিকভাবে রোগ প্রতিরোধী।'
        },
        'Lablab Bean': {
            'description': 'লাবলাব একটি বহুমুখী গ্রীষ্মকালীন ফসল। এটি গবাদি পশুর খাদ্য হিসেবেও ব্যবহৃত হয়।',
            'care': 'গ্রীষ্মকালে বপন করুন। ভালো সেচ প্রয়োজন। পোকামাকড় থেকে রক্ষা করুন।'
        },
        'Rice Bean': {
            'description': 'চালের ডাল একটি প্রোটিন সমৃদ্ধ গ্রীষ্মকালীন ফসল। এটি ভাতের মতো দেখতে।',
            'care': 'গ্রীষ্মকালে বপন করুন। ভালো নিষ্কাশনযুক্ত মাটি প্রয়োজন। নিয়মিত সেচ দিন।'
        },
        'Grass Pea (Khesari)': {
            'description': 'খেসারি একটি শীতকালীন ফসল যা খরা সহনশীল। এটি প্রোটিন সমৃদ্ধ কিন্তু বিষাক্ত হতে পারে।',
            'care': 'শীতকালে বপন করুন। কম সেচ প্রয়োজন। সঠিক রান্না করে খান।'
        },
        'Soybean': {
            'description': 'সয়াবিন একটি প্রোটিন সমৃদ্ধ গ্রীষ্মকালীন ফসল। এটি তেল এবং খাদ্য হিসেবে ব্যবহৃত হয়।',
            'care': 'গ্রীষ্মকালে বপন করুন। ভালো সেচ প্রয়োজন। পোকামাকড় থেকে রক্ষা করুন।'
        },
        'Lima Bean': {
            'description': 'লিমা ডাল একটি বড় আকারের গ্রীষ্মকালীন ফসল। এটি প্রোটিন এবং কার্বোহাইড্রেট সমৃদ্ধ।',
            'care': 'গ্রীষ্মকালে বপন করুন। উষ্ণ আবহাওয়া প্রয়োজন। নিয়মিত সেচ দিন।'
        },
        'Winged Bean': {
            'description': 'উইংড বিন একটি বহুমুখী গ্রীষ্মকালীন ফসল। এটির পাতা, ফুল এবং ডাল খাওয়া যায়।',
            'care': 'গ্রীষ্মকালে বপন করুন। ভালো সেচ প্রয়োজন। পোকামাকড় থেকে রক্ষা করুন।'
        },
        'Velvet Bean': {
            'description': 'ভেলভেট বিন একটি গ্রীষ্মকালীন ফসল যা মাটির উর্বরতা বাড়ায়।',
            'care': 'গ্রীষ্মকালে বপন করুন। কম পরিচর্যা প্রয়োজন। প্রাকৃতিকভাবে রোগ প্রতিরোধী।'
        },
        'Sword Bean': {
            'description': 'সোর্ড বিন একটি লতানো গ্রীষ্মকালীন ফসল। এটি দীর্ঘ ডাল উৎপাদন করে।',
            'care': 'গ্রীষ্মকালে বপন করুন। ভালো সেচ প্রয়োজন। লতা বাঁধার জন্য সাপোর্ট দিন।'
        },
        'Cluster Bean (Guar)': {
            'description': 'গুয়ার একটি খরা সহনশীল গ্রীষ্মকালীন ফসল। এটি শিল্পে ব্যবহৃত হয়।',
            'care': 'গ্রীষ্মকালে বপন করুন। কম পানিতে বেঁচে থাকে। নাইট্রোজেন সার ব্যবহার করুন।'
        }
    }

    crop_key = crop_name.split(' (')[0]  # Remove English name in parentheses
    if crop_key in descriptions:
        desc = descriptions[crop_key]
        return f"{desc['description']} {desc['care']}"
    else:
        return f"{crop_name} একটি {season} ফসল। এটি প্রোটিন সমৃদ্ধ এবং মাটির উর্বরতা বাড়ায়। নিয়মিত সেচ এবং পরিচর্যা করুন।"

@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def weather_advice(request, crop_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can get weather advice'}, status=status.HTTP_403_FORBIDDEN)

    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Fetch weather data (using Dhaka as default location)
        api_key = settings.WEATHER_API_KEY
        weather_url = f'http://api.weatherapi.com/v1/current.json?key={api_key}&q=Dhaka'
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        if weather_response.status_code != 200:
            # Mock data for demo purposes with extreme conditions to trigger alerts
            temp = 42  # High temperature to trigger alert
            humidity = 95  # High humidity to trigger alert
            weather_desc = 'Rain'  # Rain to trigger alert
        else:
            temp = weather_data['current']['temp_c']
            humidity = weather_data['current']['humidity']
            weather_desc = weather_data['current']['condition']['text']

        # Generate advice based on crop and weather
        advice, alerts = generate_crop_advice(crop.name, temp, humidity, weather_desc)

        return Response({
            'crop': crop.name,
            'weather': {
                'temperature': temp,
                'humidity': humidity,
                'description': weather_desc
            },
            'advice': advice,
            'alerts': alerts,
            'trends': [
                {'date': '2023-10-01', 'temperature': temp + 2, 'humidity': humidity + 5},
                {'date': '2023-10-02', 'temperature': temp - 1, 'humidity': humidity - 3},
                {'date': '2023-10-03', 'temperature': temp + 1, 'humidity': humidity + 2},
                {'date': '2023-10-04', 'temperature': temp, 'humidity': humidity},
                {'date': '2023-10-05', 'temperature': temp - 2, 'humidity': humidity - 1},
                {'date': '2023-10-06', 'temperature': temp + 3, 'humidity': humidity + 4},
                {'date': '2023-10-07', 'temperature': temp, 'humidity': humidity + 1},
            ]
        })
    except Exception as e:
        return Response({'error': 'Weather service unavailable'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_crop_advice(crop_name, temp, humidity, weather_desc):
    # Enhanced fallback advice with specific problems and solutions based on weather conditions
    advice = f"আজকের আবহাওয়া: তাপমাত্রা {temp}°C, আর্দ্রতা {humidity}%, {weather_desc}।\n\n"

    alerts = []

    # Temperature-based problems and solutions
    if temp > 40:
        advice += "উচ্চ তাপমাত্রা: সম্ভাব্য সমস্যা - গাছের পাতা ঝলসানো, ফুল ঝরে যাওয়া, ফলের গুণগত মান কমে যাওয়া।\nকী করবেন: সকালে বা সন্ধ্যায় সেচ দিন। ছায়া প্রদানের ব্যবস্থা করুন (শেড নেট ব্যবহার)। মালচিং করে মাটি ঠান্ডা রাখুন।\n"
        alerts.append("সতর্কতা: উচ্চ তাপমাত্রা! গাছের পাতা ঝলসানোর ঝুঁকি রয়েছে। অবিলম্বে ছায়া প্রদান করুন।")
    elif temp < 10:
        advice += "নিম্ন তাপমাত্রা: সম্ভাব্য সমস্যা - গাছের বৃদ্ধি বন্ধ হয়ে যাওয়া, ফুল না ফোটা, ফলের ক্ষতি।\nকী করবেন: রাতে সেচ কমিয়ে দিন। গাছকে ঠান্ডা থেকে রক্ষা করুন (প্লাস্টিক শিট ব্যবহার)। সকালে সেচ দিন যখন তাপমাত্রা বাড়ে।\n"
        alerts.append("সতর্কতা: নিম্ন তাপমাত্রা! গাছের বৃদ্ধি বন্ধ হয়ে যাওয়ার ঝুঁকি রয়েছে। গাছকে ঢেকে রাখুন।")
    else:
        advice += "আদর্শ তাপমাত্রা: নিয়মিত সেচ চালিয়ে যান।\n"

    # Humidity-based problems and solutions
    if humidity > 90:
        advice += "উচ্চ আর্দ্রতা: সম্ভাব্য সমস্যা - ছত্রাক রোগ (পাউডারি মিলডিউ, ডাউনি মিলডিউ), ব্যাকটেরিয়া রোগ, ফল পচে যাওয়া।\nকী করবেন: ভালো বায়ু চলাচল নিশ্চিত করুন। ছত্রাক রোগের জন্য পর্যবেক্ষণ করুন এবং প্রয়োজনে ফাংগিসাইড ব্যবহার করুন। গাছের মধ্যে পর্যাপ্ত দূরত্ব রাখুন।\n"
        alerts.append("সতর্কতা: উচ্চ আর্দ্রতা! ছত্রাক রোগের ঝুঁকি বেশি। বায়ু চলাচল নিশ্চিত করুন এবং ফাংগিসাইড প্রয়োগ করুন।")
    elif humidity < 30:
        advice += "নিম্ন আর্দ্রতা: সম্ভাব্য সমস্যা - মাটি শুষ্ক হয়ে যাওয়া, গাছের পাতা ঝলসানো, ফলের আকার ছোট হয়ে যাওয়া।\nকী করবেন: সেচের পরিমাণ বাড়ান। মাটি শুষ্ক না হয় তা নিশ্চিত করুন। মালচিং করে আর্দ্রতা ধরে রাখুন।\n"
        alerts.append("সতর্কতা: নিম্ন আর্দ্রতা! মাটি শুষ্ক হয়ে যাওয়ার ঝুঁকি রয়েছে। অতিরিক্ত সেচ দিন।")
    else:
        advice += "আদর্শ আর্দ্রতা: স্বাভাবিক সেচ চালিয়ে যান।\n"

    # Weather condition specific problems and solutions
    weather_lower = weather_desc.lower()
    if 'rain' in weather_lower or 'shower' in weather_lower:
        advice += "বৃষ্টি: সম্ভাব্য সমস্যা - জলাবদ্ধতা, মূল পচে যাওয়া, পোকামাকড়ের আক্রমণ বৃদ্ধি।\nকী করবেন: অতিরিক্ত সেচ এড়িয়ে চলুন। জলাবদ্ধতা থেকে রক্ষা করুন (নিষ্কাশন ব্যবস্থা উন্নত করুন)। বৃষ্টির পরে মাটি পরীক্ষা করে সেচ দিন।\n"
        alerts.append("সতর্কতা: বৃষ্টি! জলাবদ্ধতা এবং মূল পচে যাওয়ার ঝুঁকি রয়েছে। নিষ্কাশন ব্যবস্থা পরীক্ষা করুন।")
    elif 'sunny' in weather_lower or 'clear' in weather_lower:
        advice += "রৌদ্রজ্জ্বল: সম্ভাব্য সমস্যা - গাছের পাতা ঝলসানো, মাটি দ্রুত শুষ্ক হয়ে যাওয়া।\nকী করবেন: সকালে বা সন্ধ্যায় সেচ দিন। গাছের পাতা রক্ষা করুন (ছায়া প্রদান)। মাটি আর্দ্র রাখুন।\n"
    elif 'cloud' in weather_lower:
        advice += "মেঘলা: সম্ভাব্য সমস্যা - গাছের বৃদ্ধি ধীর হয়ে যাওয়া, ফুল কম ফোটা।\nকী করবেন: সেচের সময়সূচী স্বাভাবিক রাখুন। রোদ এলে অতিরিক্ত সেচ দিন।\n"
    elif 'wind' in weather_lower:
        advice += "বাতাস: সম্ভাব্য সমস্যা - গাছ ভেঙে যাওয়া, মাটি শুষ্ক হয়ে যাওয়া।\nকী করবেন: গাছকে শক্ত করে বাঁধুন। মাটি শুষ্ক না হয় তা দেখুন। বায়ু ভাঙা প্রতিবন্ধক ব্যবহার করুন।\n"
        alerts.append("সতর্কতা: প্রবল বাতাস! গাছ ভেঙে যাওয়ার ঝুঁকি রয়েছে। গাছকে শক্ত করে বাঁধুন।")

    # Crop-specific additional problems and solutions
    crop_lower = crop_name.lower()
    if 'rice' in crop_lower:
        advice += "\nধানের জন্য: সম্ভাব্য সমস্যা - জলাবদ্ধতা, পোকামাকড় (স্টেম বোরার), রোগ (ব্লাস্ট)।\nকী করবেন: জলাবদ্ধতা বজায় রাখুন কিন্তু অতিরিক্ত জল এড়ান। পোকামাকড়ের জন্য পর্যবেক্ষণ করুন এবং প্রয়োজনে কীটনাশক ব্যবহার করুন।"
    elif 'lentil' in crop_lower or 'masoor' in crop_lower:
        advice += "\nমসুরের জন্য: সম্ভাব্য সমস্যা - মাটি নিষ্কাশন সমস্যা, ফুল না ফোটা, পোকামাকড়।\nকী করবেন: মাটি ভালোভাবে নিষ্কাশন নিশ্চিত করুন। ফুল ধরার সময় সেচ কমান। পোকামাকড় প্রতিরোধের জন্য প্রাকৃতিক উপায় ব্যবহার করুন।"
    elif 'wheat' in crop_lower:
        advice += "\nগমের জন্য: সম্ভাব্য সমস্যা - রাস্ট রোগ, পোকামাকড় (এফিড), শীতের ক্ষতি।\nকী করবেন: শীতকালীন ফসল হিসেবে ঠান্ডা আবহাওয়া উপভোগ করে। নিয়মিত পর্যবেক্ষণ করুন। রোগ প্রতিরোধের জন্য ফাংগিসাইড ব্যবহার করুন।"
    else:
        advice += f"\n{crop_name} এর জন্য: সাধারণ পরিচর্যা চালিয়ে যান এবং আবহাওয়া পরিবর্তনের সাথে সেচ সমন্বয় করুন। প্রয়োজনে স্থানীয় কৃষি অফিসের পরামর্শ নিন।"

    return advice, alerts

@api_view(['GET', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def chat_history(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    # Relaxed permission
    # if request.user.role != 'farmer':
    #     return Response({'error': 'Only farmers can view chat history'}, status=status.HTTP_403_FORBIDDEN)
    
    user = request.user

    chat_messages = ChatMessage.objects.filter(user=user).order_by('created_at')
    serializer = ChatMessageSerializer(chat_messages, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ai(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    # Relaxed permission
    # if request.user.role != 'farmer':
    #     return Response({'error': 'Only farmers can chat'}, status=status.HTTP_403_FORBIDDEN)
    
    user = request.user

    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Save the chat message
    chat_message = ChatMessage.objects.create(user=user, message=message, image=request.FILES.get('image'))

    # Generate response using DeepSeek, Google Gemini or OpenAI as fallback
    deepseek_api_key = settings.DEEPSEEK_API_KEY
    gemini_api_key = settings.GEMINI_API_KEY
    openai_api_key = settings.OPENAI_API_KEY

    response_text = None

    # 1. Try DeepSeek
    if deepseek_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

            # Get crop details for context
            crops = Crop.objects.all()
            crop_info = "উপলব্ধ ফসলের তথ্য:\n"
            for crop in crops:
                description = generate_crop_description(crop.name, crop.season)
                crop_info += f"- {crop.name} ({crop.season}): {description}\n"

            system_prompt = f"আপনি একজন কৃষি বিশেষজ্ঞ। বাংলায় উত্তর দিন। কৃষকদের সাহায্য করুন। নিচে উপলব্ধ ফসলের তথ্য দেওয়া হলো:\n{crop_info}"

            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": message})

            # DeepSeek text-only for now
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )

            response_text = response.choices[0].message.content.strip()
            logger.info("Used DeepSeek for chat response")

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            pass

    # 2. Try Gemini if DeepSeek failed
    if not response_text and gemini_api_key and gemini_api_key != 'your_gemini_api_key_here':
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            
            # Get crop details for context (if not already generated)
            if 'crop_info' not in locals():
                crops = Crop.objects.all()
                crop_info = "উপলব্ধ ফসলের তথ্য:\n"
                for crop in crops:
                    description = generate_crop_description(crop.name, crop.season)
                    crop_info += f"- {crop.name} ({crop.season}): {description}\n"
                system_prompt = f"আপনি একজন কৃষি বিশেষজ্ঞ। বাংলায় উত্তর দিন। কৃষকদের সাহায্য করুন। নিচে উপলব্ধ ফসলের তথ্য দেওয়া হলো:\n{crop_info}"

            # For Gemini, combine system prompt with user message
            full_prompt = f"{system_prompt}\n\nUser: {message}"

            model = genai.GenerativeModel("gemini-1.5-flash")

            if chat_message.image:
                import PIL.Image
                img = PIL.Image.open(chat_message.image.path)
                response = model.generate_content([full_prompt, img])
            else:
                response = model.generate_content(full_prompt)

            response_text = response.text.strip()
            logger.info("Used Gemini for chat response")

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            pass

    # 3. Try OpenAI if others failed
    if not response_text and openai_api_key and openai_api_key != 'your_openai_api_key_here':
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)

            if 'crop_info' not in locals():
                crops = Crop.objects.all()
                crop_info = "উপলব্ধ ফসলের তথ্য:\n"
                for crop in crops:
                    description = generate_crop_description(crop.name, crop.season)
                    crop_info += f"- {crop.name} ({crop.season}): {description}\n"
                system_prompt = f"আপনি একজন কৃষি বিশেষজ্ঞ। বাংলায় উত্তর দিন। কৃষকদের সাহায্য করুন। নিচে উপলব্ধ ফসলের তথ্য দেওয়া হলো:\n{crop_info}"

            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": message})

            if chat_message.image:
                import base64
                image_path = chat_message.image.path
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })

            response = client.chat.completions.create(
                model="gpt-4o-mini" if chat_message.image else "gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            response_text = response.choices[0].message.content.strip()
            logger.info("Used OpenAI for chat response")

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            pass

    # 4. Final Fallback (Mock AI for testing/demo when keys fail)
    if not response_text:
        # Simple keyword-based mock responses for demo purposes
        lower_msg = message.lower()
        if 'rice' in lower_msg or 'ধান' in lower_msg:
            response_text = "ধানের ব্লাস্ট রোগ দমনে ট্রাইসাইক্লাজোল গ্রুপের ছত্রাকনাশক ব্যবহার করতে পারেন। জমিতে পানি ধরে রাখুন।"
        elif 'potato' in lower_msg or 'আলু' in lower_msg:
            response_text = "আলুর নাবি ধসা রোগ রোধে ম্যানকোজেব স্প্রে করুন। কুয়াশাচ্ছন্ন আবহাওয়ায় বিশেষ যত্ন নিন।"
        elif 'fertilizer' in lower_msg or 'সার' in lower_msg:
            response_text = "মাটি পরীক্ষা করে সার প্রয়োগ করা উত্তম। সাধারণত ইউরিয়া, টিএসপি এবং এমওপি সার নির্দিষ্ট অনুপাতে ব্যবহার করা হয়।"
        elif 'hello' in lower_msg or 'hi' in lower_msg or 'হ্যালো' in lower_msg:
            response_text = "নমস্কার! আমি আপনার কৃষি সহকারী। আপনার ফসলের সমস্যা সম্পর্কে আমাকে জানান।"
        elif 'help' in lower_msg or 'সাহায্য' in lower_msg:
            response_text = "আমি আপনাকে ফসল, সার, রোগবালাই এবং আবহাওয়া সম্পর্কে তথ্য দিয়ে সাহায্য করতে পারি।"
        elif 'weather' in lower_msg or 'আবহাওয়া' in lower_msg:
            response_text = "আবহাওয়ার পূর্বাভাস জানতে আপনার এলাকার নাম বলুন অথবা 'আবহাওয়া' ট্যাবে যান।"
        elif 'pest' in lower_msg or 'poka' in lower_msg or 'পোকামাকড়' in lower_msg:
            response_text = "পোকামাকড় দমনে জৈব বালাইনাশক ব্যবহার করা ভালো। আক্রান্ত ফসলের ছবি তুললে আমি আরও ভালো পরামর্শ দিতে পারব।"
        else:
            response_text = "আমি আপনার কথাটি বুঝতে পারিনি। দয়া করে কৃষি, ফসল, বা রোগবালাই সম্পর্কে প্রশ্ন করুন। যেমন: 'ধানের ব্লাস্ট রোগ' বা 'আলুর সার'।"

    # Update the chat message with response
    chat_message.response = response_text
    chat_message.save()

    return Response({
        'message': ChatMessageSerializer(chat_message, context={'request': request}).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_health(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    user = request.user

    # Aggregate data per crop for this farmer
    from django.db.models import Count, Q
    crops_data = []
    crops = Crop.objects.all()
    for crop in crops:
        problems_count = Problem.objects.filter(farmer=user, title__icontains=crop.name.split(' ')[0]).count()
        advice_count = ChatMessage.objects.filter(user=user, message__icontains=crop.name.split(' ')[0]).count()
        latest_problem = Problem.objects.filter(farmer=user, title__icontains=crop.name.split(' ')[0]).order_by('-created_at').first()
        status = 'solved' if latest_problem and latest_problem.replies.exists() else 'pending' if problems_count > 0 else 'good'
        crops_data.append({
            'crop': crop.name,
            'problems': problems_count,
            'advice': advice_count,
            'status': status
        })
    return Response(crops_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def problem_trends(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    user = request.user

    # Problems over last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    trends = []
    current_date = start_date
    while current_date <= end_date:
        count = Problem.objects.filter(farmer=user, created_at__date=current_date).count()
        trends.append({'date': current_date.isoformat(), 'problems': count})
        current_date += timedelta(days=1)
    return Response(trends)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weather_trends(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    # Weather data over last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    weather_data = WeatherData.objects.filter(date__range=[start_date, end_date]).order_by('date')
    serializer = WeatherDataSerializer(weather_data, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advice_insights(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    user = request.user

    # Advice count per crop
    from django.db.models import Count
    insights = []
    crops = Crop.objects.all()
    for crop in crops:
        count = ChatMessage.objects.filter(user=user, message__icontains=crop.name.split(' ')[0]).count()
        if count > 0:
            insights.append({'crop': crop.name, 'advice_count': count})
    insights.sort(key=lambda x: x['advice_count'], reverse=True)
    return Response(insights[:5])  # Top 5

@api_view(['GET'])
def region_problems(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    # Problems by region
    from django.db.models import Count
    regions = User.objects.filter(role='farmer', region__isnull=False).values('region').annotate(count=Count('problems')).order_by('-count')
    return Response(list(regions))

@api_view(['GET'])
def top_crops(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    # Top crops with most problems
    from django.db.models import Count
    crops = Crop.objects.annotate(problem_count=Count('problems')).order_by('-problem_count')[:5]
    data = [{'crop': crop.name, 'problems': crop.problem_count} for crop in crops]
    return Response(data)

@api_view(['GET'])
def activity_summary(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    farmers_count = User.objects.filter(role='farmer').count()
    problems_count = Problem.objects.count()
    replies_count = Reply.objects.count()
    posts_count = Post.objects.count()
    active_farmers = User.objects.filter(role='farmer', problems__created_at__gte=timezone.now() - timedelta(days=7)).distinct().count()
    return Response({
        'farmers': farmers_count,
        'problems': problems_count,
        'replies': replies_count,
        'posts': posts_count,
        'active_farmers_week': active_farmers
    })

@api_view(['GET'])
def current_weather(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Get the latest weather data
    try:
        latest_weather = WeatherData.objects.order_by('-date').first()
        if latest_weather:
            serializer = WeatherDataSerializer(latest_weather)
            return Response(serializer.data)
        else:
            return Response({'error': 'No weather data available'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': 'Failed to fetch weather data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def current_weather_live(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Fetch live weather data from WeatherAPI.com
    try:
        api_key = settings.WEATHER_API_KEY
        if not api_key or api_key == 'your_weather_api_key_here':
            # Fallback to mock data if API key not set
            return Response({
                'temperature': 28.5,
                'humidity': 75,
                'wind_speed': 12.5,
                'condition': 'Partly cloudy',
                'advice': 'আজকের আবহাওয়া ভালো। ফসলের যত্ন নিন।'
            })

        # Get user's region if available (from auth token)
        region = 'Dhaka'  # Default
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            if token.startswith('farmer_token_'):
                try:
                    user_id = int(token.split('_')[-1])
                    user = User.objects.get(id=user_id)
                    if user.region:
                        region = user.region
                except (ValueError, User.DoesNotExist):
                    pass

        weather_url = f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={region}&aqi=no'
        weather_response = requests.get(weather_url, timeout=10)

        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            current = weather_data['current']

            # Generate simple advice based on weather
            temp = current['temp_c']
            condition = current['condition']['text'].lower()
            advice = "আজকের আবহাওয়া ভালো। ফসলের যত্ন নিন।"

            if temp > 35:
                advice = "উচ্চ তাপমাত্রা! গাছকে ছায়া প্রদান করুন এবং অতিরিক্ত সেচ দিন।"
            elif temp < 15:
                advice = "নিম্ন তাপমাত্রা! গাছকে ঢেকে রাখুন।"
            elif 'rain' in condition:
                advice = "বৃষ্টি হচ্ছে! জলাবদ্ধতা এড়িয়ে চলুন।"
            elif 'cloud' in condition:
                advice = "মেঘলা আবহাওয়া। সেচের পরিমাণ কমান।"

            return Response({
                'temperature': current['temp_c'],
                'humidity': current['humidity'],
                'wind_speed': current['wind_kph'],
                'condition': current['condition']['text'],
                'advice': advice
            })
        else:
            # Fallback to mock data on API failure
            return Response({
                'temperature': 28.5,
                'humidity': 75,
                'wind_speed': 12.5,
                'condition': 'Partly cloudy',
                'advice': 'আজকের আবহাওয়া ভালো। ফসলের যত্ন নিন।'
            })

    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request failed: {e}")
        # Fallback to mock data
        return Response({
            'temperature': 28.5,
            'humidity': 75,
            'wind_speed': 12.5,
            'condition': 'Partly cloudy',
            'advice': 'আজকের আবহাওয়া ভালো। ফসলের যত্ন নিন।'
        })
    except Exception as e:
        logger.error(f"Error fetching live weather: {e}")
        return Response({'error': 'Weather service temporarily unavailable'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# New views for Crop Season Planner

@api_view(['GET'])
def activities_list(request, crop_id):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for farmer
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if not token.startswith('farmer_token_'):
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)
    user_id = int(token.split('_')[-1])
    try:
        user = User.objects.get(id=user_id, role='farmer')
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    activities = Activity.objects.filter(crop=crop).order_by('order')
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farmer_timeline(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    timelines = Timeline.objects.filter(farmer=request.user).order_by('start_date')
    serializer = TimelineSerializer(timelines, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_timeline(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    crop_id = request.data.get('crop_id')
    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    activities = Activity.objects.filter(crop=crop).order_by('order')
    start_date = request.data.get('start_date')
    if not start_date:
        return Response({'error': 'Start date required'}, status=status.HTTP_400_BAD_REQUEST)

    from datetime import datetime, timedelta
    current_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    if not activities.exists():
        # Default activities for crops without specific activities
        default_activities = [
            {'name': 'মাটি প্রস্তুতি', 'expected_time': 7, 'is_critical': True},
            {'name': 'বীজ বপন', 'expected_time': 1, 'is_critical': True},
            {'name': 'সেচ সেটআপ', 'expected_time': 2, 'is_critical': False},
            {'name': 'সার প্রয়োগ', 'expected_time': 3, 'is_critical': False},
            {'name': 'আগাছা নিয়ন্ত্রণ', 'expected_time': 5, 'is_critical': False},
            {'name': 'কীটনাশক প্রয়োগ', 'expected_time': 2, 'is_critical': False},
            {'name': 'ফসল তোলা', 'expected_time': 3, 'is_critical': True},
        ]
        timelines_data = []
        for act in default_activities:
            end_date = current_date + timedelta(days=act['expected_time'])
            timelines_data.append({
                'activity': {'name': act['name']},
                'start_date': current_date.isoformat(),
                'end_date': end_date.isoformat(),
                'is_critical': act['is_critical']
            })
            current_date = end_date + timedelta(days=1)
        return Response(timelines_data)
    else:
        timelines = []
        for activity in activities:
            end_date = current_date + timedelta(days=int(activity.expected_time()))
            timeline = Timeline.objects.create(
                farmer=user,
                crop=crop,
                activity=activity,
                start_date=current_date,
                end_date=end_date,
                is_critical=False  # Will be calculated later
            )
            timelines.append(timeline)
            current_date = end_date + timedelta(days=1)  # Next activity starts next day

        # Calculate critical path (simplified CPM)
        calculate_critical_path(timelines)

        serializer = TimelineSerializer(timelines, many=True)
        return Response(serializer.data)

def calculate_critical_path(timelines):
    # Simplified CPM calculation
    # Mark activities with no dependencies as critical
    for timeline in timelines:
        if not timeline.activity.dependencies.exists():
            timeline.is_critical = True
            timeline.save()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request, timeline_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    try:
        timeline = Timeline.objects.get(id=timeline_id, farmer=request.user)
    except Timeline.DoesNotExist:
        return Response({'error': 'Timeline not found'}, status=status.HTTP_404_NOT_FOUND)

    percentage = request.data.get('percentage', 0)
    notes = request.data.get('notes', '')

    progress, created = Progress.objects.get_or_create(timeline=timeline)
    progress.completed_percentage = percentage
    progress.notes = notes
    progress.save()

    serializer = ProgressSerializer(progress)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_progress(request, crop_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get all timelines for this farmer and crop
    timelines = Timeline.objects.filter(farmer=request.user, crop=crop)
    if not timelines.exists():
        return Response({'progress': 0})

    # Calculate average progress
    progresses = []
    for timeline in timelines:
        try:
            progress = timeline.progress.completed_percentage
            progresses.append(progress)
        except Progress.DoesNotExist:
            progresses.append(0)  # If no progress record, assume 0

    average_progress = sum(progresses) / len(progresses) if progresses else 0
    return Response({'progress': round(average_progress, 2)})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pert_analysis(request, crop_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can access this'}, status=status.HTTP_403_FORBIDDEN)

    try:
        crop = Crop.objects.get(id=crop_id)
    except Crop.DoesNotExist:
        return Response({'error': 'Crop not found'}, status=status.HTTP_404_NOT_FOUND)

    activities = Activity.objects.filter(crop=crop)
    pert_data = []
    total_expected = 0
    total_variance = 0

    for activity in activities:
        expected = activity.expected_time()
        variance = activity.variance()
        total_expected += expected
        total_variance += variance
        pert_data.append({
            'activity': activity.name,
            'optimistic': activity.optimistic_time,
            'most_likely': activity.most_likely_time,
            'pessimistic': activity.pessimistic_time,
            'expected': round(expected, 2),
            'variance': round(variance, 2),
            'standard_deviation': round(variance ** 0.5, 2)
        })

    # Calculate project completion probability (simplified)
    import math
    target_days = total_expected + 7  # Target completion in expected + 1 week
    z_score = (target_days - total_expected) / math.sqrt(total_variance) if total_variance > 0 else 0
    probability = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

    return Response({
        'activities': pert_data,
        'project_expected': round(total_expected, 2),
        'project_variance': round(total_variance, 2),
        'project_std_dev': round(math.sqrt(total_variance), 2),
        'completion_probability': round(probability * 100, 2)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_analytics(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    from django.db.models import Count, Avg

    # Regional analytics
    regions = User.objects.filter(role='farmer', region__isnull=False).values('region').annotate(
        farmer_count=Count('id'),
        problem_count=Count('problems'),
        avg_problems=Avg('problems__id')
    ).order_by('-farmer_count')

    # Crop performance
    crops = Crop.objects.annotate(
        timeline_count=Count('timelines'),
        avg_progress=Avg('timelines__progress__completed_percentage')
    ).order_by('-timeline_count')

    # Risk assessment
    high_risk_activities = Activity.objects.filter(
        pessimistic_time__gt=30  # Activities with high uncertainty
    ).values('name', 'crop__name', 'pessimistic_time')

    return Response({
        'regional_analytics': list(regions),
        'crop_performance': list(crops.values('name', 'timeline_count', 'avg_progress')),
        'high_risk_activities': list(high_risk_activities),
        'total_timelines': Timeline.objects.count(),
        'completed_activities': Progress.objects.filter(completed_percentage=100).count()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_prices(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    # Allow farmers, buyers and experts
    if request.user.role not in ['farmer', 'buyer', 'expert']:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    # Get latest market prices (last 30 days)
    from django.utils import timezone
    from datetime import timedelta
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    prices = MarketPrice.objects.filter(date__range=[start_date, end_date]).order_by('-date', 'crop_name', 'market_name')
    serializer = MarketPriceSerializer(prices, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_market_price(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can add market prices'}, status=status.HTTP_403_FORBIDDEN)

    serializer = MarketPriceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def auto_refresh_prices(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can refresh prices'}, status=status.HTTP_403_FORBIDDEN)

    # Mock govt API data - in real implementation, this would call actual govt API
    mock_govt_data = [
        {"crop": "ধান", "market": "Dhaka", "price": 42.5, "district": "Dhaka"},
        {"crop": "গম", "market": "Rajshahi", "price": 38.0, "district": "Rajshahi"},
        {"crop": "পেঁয়াজ", "market": "Bogura", "price": 78.0, "district": "Rajshahi"},
        {"crop": "আলু", "market": "Khulna", "price": 25.0, "district": "Khulna"},
        {"crop": "টমেটো", "market": "Sylhet", "price": 45.0, "district": "Sylhet"},
    ]

    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'role': 'admin'}
    )

    updated_prices = []
    for item in mock_govt_data:
        # Update or create price record
        price, created = MarketPrice.objects.update_or_create(
            crop_name=item['crop'],
            market_name=item['market'],
            district=item['district'],
            date=timezone.now().date(),
            defaults={
                'price_per_kg': item['price'],
                'source': 'Govt API',
                'updated_by': user
            }
        )
        updated_prices.append(price)

    serializer = MarketPriceSerializer(updated_prices, many=True)
    return Response({
        'message': f'Successfully updated {len(updated_prices)} market prices from Govt API',
        'prices': serializer.data
    })

@api_view(['GET'])
def govt_api_prices(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access govt API'}, status=status.HTTP_403_FORBIDDEN)

    # Mock govt API response - in real implementation, this would call actual govt API
    govt_data = [
        {"crop": "ধান", "market": "Dhaka", "price": 42.5, "district": "Dhaka", "date": timezone.now().date()},
        {"crop": "গম", "market": "Rajshahi", "price": 38.0, "district": "Rajshahi", "date": timezone.now().date()},
        {"crop": "পেঁয়াজ", "market": "Bogura", "price": 78.0, "district": "Rajshahi", "date": timezone.now().date()},
        {"crop": "আলু", "market": "Khulna", "price": 25.0, "district": "Khulna", "date": timezone.now().date()},
        {"crop": "টমেটো", "market": "Sylhet", "price": 45.0, "district": "Sylhet", "date": timezone.now().date()},
    ]

    return Response({
        'source': 'Mock Govt Agricultural API',
        'last_updated': timezone.now().isoformat(),
        'data': govt_data
    })

@api_view(['GET'])
def welcome(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({'message': 'Welcome to the Agroby Sami API!'})

@api_view(['GET'])
@permission_classes([AllowAny])
def hello(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({'message': 'Hello! Welcome to the Agroby Sami API service.'})

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def welcome_api(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({'message': 'Welcome to the Agroby Sami API!'})

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def welcome_message(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({'message': 'Welcome to the Agroby Sami API!'})

@api_view(['GET'])
def ai_price_suggestions(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for farmer
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    token = auth_header.split(' ')[1]
    if not token.startswith('farmer_token_'):
        return Response({'error': 'Only farmers can get AI suggestions'}, status=status.HTTP_403_FORBIDDEN)

    crop_name = request.GET.get('crop', '').strip()
    if not crop_name:
        return Response({'error': 'Crop name is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Get recent price data for the crop
    from django.utils import timezone
    from datetime import timedelta
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=15)

    prices = MarketPrice.objects.filter(
        crop_name__icontains=crop_name,
        date__range=[start_date, end_date]
    ).order_by('-date')[:10]

    if not prices.exists():
        return Response({
            'suggestion': f'{crop_name} এর জন্য পর্যাপ্ত দামের তথ্য নেই।',
            'confidence': 0
        })

    # Calculate trend
    price_list = list(prices.values_list('price_per_kg', flat=True))
    if len(price_list) >= 2:
        latest_price = price_list[0]
        previous_price = price_list[1]
        change = latest_price - previous_price
        change_percent = (change / previous_price) * 100 if previous_price > 0 else 0

        if change > 0:
            trend = "ঊর্ধ্বমুখী"
            advice = f"{crop_name} এর দাম বাড়ছে। গত ১৫ দিনে {change_percent:.1f}% বৃদ্ধি। বিক্রি কিছুটা দেরি করুন।"
        elif change < 0:
            trend = "নিম্নমুখী"
            advice = f"{crop_name} এর দাম কমছে। গত ১৫ দিনে {abs(change_percent):.1f}% হ্রাস। যত তাড়াতাড়ি সম্ভব বিক্রি করুন।"
        else:
            trend = "স্থিতিশীল"
            advice = f"{crop_name} এর দাম স্থিতিশীল। বর্তমান বাজার পরিস্থিতি অনুযায়ী সিদ্ধান্ত নিন।"
    else:
        trend = "অজানা"
        advice = f"{crop_name} এর জন্য পর্যাপ্ত তথ্য নেই। বাজার পর্যবেক্ষণ চালিয়ে যান।"

    # Use OpenAI for enhanced suggestions if available
    api_key = settings.OPENAI_API_KEY
    if api_key and api_key != 'your_openai_api_key_here':
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            prompt = f"""
            আপনি একজন কৃষি বিশেষজ্ঞ। {crop_name} ফসলের বর্তমান বাজার পরিস্থিতি বিশ্লেষণ করে বাংলায় সাজেস্ট করুন।
            দামের ট্রেন্ড: {trend}
            সাম্প্রতিক দাম: {latest_price if 'latest_price' in locals() else 'অজানা'} টাকা/কেজি
            পরামর্শ দিন কখন বিক্রি করা উচিত এবং কেন।
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )

            ai_advice = response.choices[0].message.content.strip()
            return Response({
                'suggestion': ai_advice,
                'trend': trend,
                'confidence': 0.8,
                'data_points': len(price_list)
            })
        except Exception as e:
            print(f"OpenAI API error: {e}")
            pass

    return Response({
        'suggestion': advice,
        'trend': trend,
        'confidence': 0.6,
        'data_points': len(price_list)
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expense_calculations_list(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role not in ['farmer', 'expert']:
        return Response({'error': 'Only farmers and experts can access expense calculations'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        if user.role == 'farmer':
            calculations = ExpenseCalculation.objects.filter(farmer=user).order_by('-created_at')
        else:  # expert
            calculations = ExpenseCalculation.objects.all().order_by('-created_at')
        serializer = ExpenseCalculationSerializer(calculations, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        try:
            if user.role == 'farmer':
                serializer = ExpenseCalculationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(farmer=user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:  # expert
                farmer_id = request.data.get('farmer_id')
                if not farmer_id:
                    return Response({'error': 'farmer_id is required for experts'}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    farmer = User.objects.get(id=farmer_id, role='farmer')
                except User.DoesNotExist:
                    return Response({'error': 'Invalid farmer_id'}, status=status.HTTP_404_NOT_FOUND)
                serializer = ExpenseCalculationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(farmer=farmer)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in expense_calculations_list: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'error': f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def expense_calculation_detail(request, calculation_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role not in ['farmer', 'expert']:
        return Response({'error': 'Only farmers and experts can access expense calculations'}, status=status.HTTP_403_FORBIDDEN)

    try:
        if user.role == 'farmer':
            calculation = ExpenseCalculation.objects.get(id=calculation_id, farmer=user)
        else:  # expert
            calculation = ExpenseCalculation.objects.get(id=calculation_id)
    except ExpenseCalculation.DoesNotExist:
        return Response({'error': 'Expense calculation not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ExpenseCalculationSerializer(calculation)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ExpenseCalculationSerializer(calculation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        calculation.delete()
        return Response({'message': 'Expense calculation deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_recommendations(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'farmer':
        return Response({'error': 'Only farmers can get crop recommendations'}, status=status.HTTP_403_FORBIDDEN)

    soil_type = request.GET.get('soil_type')
    season = request.GET.get('season')
    region = request.GET.get('region')

    if not soil_type or not season:
        return Response({'error': 'soil_type and season are required'}, status=status.HTTP_400_BAD_REQUEST)

    recommendations = CropRecommendation.objects.filter(
        soil_type=soil_type,
        season=season
    )
    if region:
        recommendations = recommendations.filter(region__icontains=region)

    serializer = CropRecommendationSerializer(recommendations, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    logger.info(f"Request: {request.method} {request.path}")
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    logger.info(f"Request: {request.method} {request.path}")
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

    notification.is_read = True
    notification.save()
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    # Check if admin (or potentially expert/system)
    if request.user.role != 'admin' and request.user.role != 'expert':
        return Response({'error': 'Only admins or experts can create notifications'}, status=status.HTTP_403_FORBIDDEN)

    # Handle Broadcast (if no specific user provided)
    data = request.data
    if 'user' not in data and 'user_id' not in data:
        try:
            count = 0
            # Broadcast to all users
            for recipient in User.objects.all():
                Notification.objects.create(
                    user=recipient,
                    title=data.get('title'),
                    message=data.get('message'),
                    notification_type=data.get('notification_type', 'system_reminder'),
                    priority=data.get('priority', 'medium')
                )
                count += 1
            return Response({'message': f'Broadcast sent to {count} users'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    serializer = NotificationSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Agri-Doctor Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_analyze_problem(request, problem_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role != 'farmer':
        return Response({'error': 'Only farmers can analyze problems'}, status=status.HTTP_403_FORBIDDEN)

    try:
        problem = Problem.objects.get(id=problem_id, farmer=user)
    except Problem.DoesNotExist:
        return Response({'error': 'Problem not found'}, status=status.HTTP_404_NOT_FOUND)

    if not problem.image:
        return Response({'error': 'Problem must have an image for AI analysis'}, status=status.HTTP_400_BAD_REQUEST)

    # Use OpenAI Vision API for analysis
    api_key = settings.OPENAI_API_KEY
    if api_key == 'your_openai_api_key_here':
        # Mock AI analysis for demo
        ai_analysis = f"এই ছবিতে {problem.crop_type or 'ফসলের'} সম্ভাব্য রোগ দেখা যাচ্ছে। পাতায় দাগ এবং ক্ষতি লক্ষ্য করা যায়।"
        recommended_treatment = "ফাংগিসাইড স্প্রে করুন এবং আক্রান্ত পাতা অপসারণ করুন।"
        preventive_measures = "নিয়মিত পরিচর্যা করুন এবং রোগ প্রতিরোধক ব্যবহার করুন।"
        confidence_score = 0.75
    else:
        try:
            from openai import OpenAI
            import base64

            client = OpenAI(api_key=api_key)

            # Read and encode image
            with open(problem.image.path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = f"""
            আপনি একজন কৃষি বিশেষজ্ঞ। এই ছবিটি বিশ্লেষণ করে বাংলায় বিস্তারিত রোগ নির্ণয় এবং চিকিৎসা পরামর্শ দিন।
            ফসলের ধরন: {problem.crop_type or 'অজানা'}
            সমস্যার বিবরণ: {problem.description}

            বিশ্লেষণে অন্তর্ভুক্ত করুন:
            1. রোগের নাম এবং লক্ষণ
            2. কারণ
            3. চিকিৎসা পদ্ধতি
            4. প্রতিরোধ ব্যবস্থা
            5. আত্মবিশ্বাসের স্কোর (0-1)
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )

            ai_response = response.choices[0].message.content.strip()

            # Parse the response (simplified parsing)
            ai_analysis = ai_response
            recommended_treatment = "চিকিৎসা পরামর্শ উপরে দেওয়া হয়েছে।"
            preventive_measures = "প্রতিরোধ ব্যবস্থা উপরে দেওয়া হয়েছে।"
            confidence_score = 0.85

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            ai_analysis = "AI বিশ্লেষণ করা সম্ভব হয়নি। পরে আবার চেষ্টা করুন।"
            recommended_treatment = "বিশেষজ্ঞের পরামর্শ নিন।"
            preventive_measures = "নিয়মিত পর্যবেক্ষণ করুন।"
            confidence_score = 0.0

    # Update problem status and create solution
    problem.status = 'ai_completed'
    problem.ai_solution = ai_analysis
    problem.save()

    solution, created = ProblemSolution.objects.get_or_create(
        problem=problem,
        defaults={
            'ai_analysis': ai_analysis,
            'recommended_treatment': recommended_treatment,
            'preventive_measures': preventive_measures,
            'confidence_score': confidence_score
        }
    )

    if not created:
        solution.ai_analysis = ai_analysis
        solution.recommended_treatment = recommended_treatment
        solution.preventive_measures = preventive_measures
        solution.confidence_score = confidence_score
        solution.save()

    # Create notification for farmer
    Notification.objects.create(
        user=user,
        title='AI বিশ্লেষণ সম্পন্ন',
        message=f'আপনার সমস্যা (ID: {problem.tracking_id}) এর AI বিশ্লেষণ সম্পন্ন হয়েছে।',
        priority='medium',
        notification_type='system_reminder'
    )

    return Response({
        'message': 'AI analysis completed',
        'problem': ProblemSerializer(problem, context={'request': request}).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def expert_review_problem(request, problem_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role != 'expert':
        return Response({'error': 'Only experts can review problems'}, status=status.HTTP_403_FORBIDDEN)

    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        return Response({'error': 'Problem not found'}, status=status.HTTP_404_NOT_FOUND)

    expert_analysis = request.data.get('expert_analysis', '').strip()
    recommended_treatment = request.data.get('recommended_treatment', '').strip()
    preventive_measures = request.data.get('preventive_measures', '').strip()

    if not expert_analysis:
        return Response({'error': 'Expert analysis is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Update problem
    problem.status = 'expert_completed'
    problem.expert_solution = expert_analysis
    problem.assigned_expert = user
    problem.solution_date = timezone.now()
    problem.save()

    # Update or create solution
    solution, created = ProblemSolution.objects.get_or_create(
        problem=problem,
        defaults={
            'expert_analysis': expert_analysis,
            'recommended_treatment': recommended_treatment,
            'preventive_measures': preventive_measures
        }
    )

    if not created:
        solution.expert_analysis = expert_analysis
        solution.recommended_treatment = recommended_treatment
        solution.preventive_measures = preventive_measures
        solution.save()

    # Create notification for farmer
    Notification.objects.create(
        user=problem.farmer,
        title='বিশেষজ্ঞ পর্যালোচনা সম্পন্ন',
        message=f'আপনার সমস্যা (ID: {problem.tracking_id}) এর বিশেষজ্ঞ পর্যালোচনা সম্পন্ন হয়েছে।',
        priority='high',
        notification_type='admin_reply'
    )

    return Response({
        'message': 'Expert review completed',
        'problem': ProblemSerializer(problem, context={'request': request}).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farmer_problem_results(request, problem_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role != 'farmer':
        return Response({'error': 'Only farmers can view problem results'}, status=status.HTTP_403_FORBIDDEN)

    try:
        problem = Problem.objects.get(id=problem_id, farmer=user)
    except Problem.DoesNotExist:
        return Response({'error': 'Problem not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProblemSerializer(problem, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expert_pending_problems(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'expert':
        return Response({'error': 'Only experts can view pending problems'}, status=status.HTTP_403_FORBIDDEN)

    problems = Problem.objects.filter(Q(status='ai_completed') | Q(status='submitted')).order_by('-created_at')
    serializer = ProblemSerializer(problems, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expert_knowledge_base(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    try:
        # Allow experts and farmers (farmers can view, experts can add/view)
        if 'expert' not in request.user.role and request.method == 'POST':
            return Response({'error': 'Only experts can add knowledge'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            items = KnowledgeBase.objects.all().order_by('-created_at')
            data = [{
                'id': item.id,
                'title': item.title,
                'category': item.category,
                'content': item.content,
                'created_at': item.created_at,
                'author_name': item.author.username if item.author else "Unknown" 
            } for item in items]
            return Response(data)
        
        elif request.method == 'POST':
            title = request.data.get('title')
            content = request.data.get('content')
            category = request.data.get('category')
            
            if not title or not content:
                 return Response({'error': 'Title and content are required'}, status=status.HTTP_400_BAD_REQUEST)

            item = KnowledgeBase.objects.create(
                author=request.user,
                title=title,
                content=content,
                category=category
            )
            
            return Response({
                'id': item.id,
                'title': item.title,
                'category': item.category,
                'content': item.content,
                'created_at': item.created_at
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Error in expert_knowledge_base: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expert_reviews(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    if request.user.role != 'expert':
        return Response({'error': 'Only experts can access reviews'}, status=status.HTTP_403_FORBIDDEN)

    # Mock data for reviews
    reviews = [
        {
            'id': 1,
            'problem_title': 'ধানের পাতায় দাগ',
            'rating': 5,
            'comment': 'খুব ভালো পরামর্শ। ধন্যবাদ।',
            'reviewer_name': 'রহিম ফার্মার',
            'created_at': timezone.now().isoformat()
        },
        {
            'id': 2,
            'problem_title': 'আলুর পচন',
            'rating': 4,
            'comment': 'উপকারী ছিল।',
            'reviewer_name': 'করিম ফার্মার',
            'created_at': timezone.now().isoformat()
        }
    ]
    return Response(reviews)

# Admin Views

@api_view(['GET'])
def admin_user_metrics(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    total_farmers = User.objects.filter(role='farmer').count()
    active_farmers = User.objects.filter(role='farmer', problems__created_at__gte=timezone.now() - timedelta(days=7)).distinct().count()
    total_experts = User.objects.filter(role='expert').count()

    return Response({
        'total_farmers': total_farmers,
        'active_farmers': active_farmers,
        'total_experts': total_experts
    })

@api_view(['GET'])
def admin_farmer_posts(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    # Get recent farmer posts/problems with replies
    posts = Post.objects.all().order_by('-created_at')[:20]
    problems = Problem.objects.all().order_by('-created_at')[:20]

    farmer_posts = []

    # Process posts
    for post in posts:
        replies = Reply.objects.filter(problem__isnull=True, post=post).count()
        farmer_posts.append({
            'id': post.id,
            'farmer_name': post.author.username if post.author else 'Unknown',
            'type': 'post',
            'title': post.title,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'date': post.created_at.strftime('%Y-%m-%d'),
            'replies': replies
        })

    # Process problems
    for problem in problems:
        replies = Reply.objects.filter(problem=problem).count()
        farmer_posts.append({
            'id': problem.id,
            'farmer_name': problem.farmer.username if problem.farmer else 'Unknown',
            'type': 'problem',
            'title': problem.title,
            'content': problem.description[:100] + '...' if len(problem.description) > 100 else problem.description,
            'date': problem.created_at.strftime('%Y-%m-%d'),
            'replies': replies
        })

    # Sort by date descending
    farmer_posts.sort(key=lambda x: x['date'], reverse=True)

    return Response(farmer_posts[:20])

@api_view(['GET', 'POST', 'PUT'])
def admin_product_prices(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Get current market prices
        prices = MarketPrice.objects.filter(date=timezone.now().date()).order_by('crop_name')
        data = []
        for price in prices:
            data.append({
                'id': price.id,
                'crop_name': price.crop_name,
                'market_name': price.market_name,
                'price_per_kg': price.price_per_kg,
                'district': price.district
            })
        return Response(data)

    elif request.method in ['POST', 'PUT']:
        crop_name = request.data.get('crop_name')
        market_name = request.data.get('market_name')
        price_per_kg = request.data.get('price_per_kg')
        district = request.data.get('district', market_name)

        if not all([crop_name, market_name, price_per_kg]):
            return Response({'error': 'crop_name, market_name, and price_per_kg are required'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'admin'}
        )

        # Update or create price
        price, created = MarketPrice.objects.update_or_create(
            crop_name=crop_name,
            market_name=market_name,
            district=district,
            date=timezone.now().date(),
            defaults={
                'price_per_kg': price_per_kg,
                'source': 'Admin Manual',
                'updated_by': user
            }
        )

        return Response({
            'id': price.id,
            'crop_name': price.crop_name,
            'market_name': price.market_name,
            'price_per_kg': price.price_per_kg,
            'district': price.district,
            'message': 'Price updated successfully'
        })

@api_view(['POST'])
def admin_create_notice(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Auth check for admin
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    token = auth_header.split(' ')[1]
    if token != 'admin_token':
        return Response({'error': 'Only admins can create notices'}, status=status.HTTP_403_FORBIDDEN)

    title = request.data.get('title', '').strip()
    message = request.data.get('message', '').strip()
    priority = request.data.get('priority', 'medium')
    target_roles = request.data.get('target_roles', ['farmer', 'expert', 'buyer'])

    if not title or not message:
        return Response({'error': 'Title and message are required'}, status=status.HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'role': 'admin'}
    )

    # Create notifications for all users with target roles
    created_count = 0
    for role in target_roles:
        users = User.objects.filter(role=role)
        for target_user in users:
            Notification.objects.create(
                user=target_user,
                title=title,
                message=message,
                priority=priority,
                notification_type='admin_announcement'
            )
            created_count += 1

    return Response({
        'message': f'Notice sent to {created_count} users successfully',
        'title': title,
        'target_roles': target_roles
    })

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def welcome_endpoint(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({'message': 'Welcome to the Agroby Sami API!'})

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def api_root(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({'message': 'Welcome to the Agroby Sami API!'})

@api_view(['GET'])
@permission_classes([AllowAny])
def welcome_with_metadata(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({
        'message': 'Welcome to the Agroby Sami API!',
        'method': request.method,
        'path': request.path
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def welcome_logged(request):
    logger.info(f"Request: {request.method} {request.path}")
    return Response({
        'message': 'Welcome to the Agroby Sami API!',
        'method': request.method,
        'path': request.path
    })

# Market and Buyer Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_products(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    # Start with available products
    queryset = ProductPost.objects.filter(status='available')

    # Filter by crop name if provided
    crop_name = request.GET.get('crop', '').strip()
    if crop_name:
        queryset = queryset.filter(crop_name__icontains=crop_name)
    
    # Filter by location if provided
    location = request.GET.get('location', '').strip()
    if location:
        queryset = queryset.filter(location__icontains=location)

    # Status filter (optional, but good to have)
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # user filter (optional, for 'my products')
    farmer_id = request.GET.get('farmer_id')
    if farmer_id:
        queryset = queryset.filter(farmer_id=farmer_id)

    # Sort by price ascending to show "Best Price" (lowest) first
    # Secondary sort by date_posted descending (newest first)
    queryset = queryset.order_by('price', '-date_posted')

    data = []
    for p in queryset:
        data.append({
            'id': p.id,
            'name': p.crop_name, # Frontend expects 'name'
            'farmer_name': p.farmer.username, # Frontend expects 'farmer_name'
            'price': float(p.price),
            'quantity': p.quantity,
            'location': p.location,
            'category': 'vegetables', # Mock category or infer
            'image': None, # Image field not in ProductPost yet
            'posted_at': p.date_posted
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_list(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    # Fetch real data from ProductPost
    posts = ProductPost.objects.filter(status='available').order_by('-date_posted')
    data = []
    for p in posts:
        data.append({
            'id': p.id,
            'crop_name': p.crop_name,
            'quantity': p.quantity,
            'price': float(p.price),
            'location': p.location,
            'farmer_name': p.farmer.username,
            'farmer_phone': p.farmer.phone if p.farmer.phone else "N/A",
            'farmer_id': p.farmer.id,
            'is_own': p.farmer.id == request.user.id
        })
    return Response(data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_market_post(request, pk):
    logger.info(f"Request: {request.method} {request.path}")
    
    try:
        post = ProductPost.objects.get(pk=pk)
    except ProductPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

    if post.farmer != request.user:
        return Response({'error': 'You can only delete your own posts'}, status=status.HTTP_403_FORBIDDEN)

    post.delete()
    return Response({'message': 'Post deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def buyer_orders(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Allow farmers to see their purchase orders too (if they buy seeds/etc in future)
    if request.user.role not in ['buyer', 'admin', 'farmer']:
         return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Fetch real orders where user is buyer
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
        data = []
        for order in orders:
            data.append({
                'id': order.id,
                'crop_name': order.product_post.crop_name,
                'quantity': order.quantity,
                'total_price': float(order.total_price),
                'status': order.status,
                'created_at': order.created_at
            })
        return Response(data)
    elif request.method == 'POST':
        # Create new order
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        if not product_id or not quantity:
            return Response({'error': 'product_id and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)
        # Mock order creation
        order = {
            'id': 3,
            'product_name': 'নতুন পণ্য',
            'quantity': quantity,
            'price': 100.0,
            'status': 'pending',
            'estimated_delivery': '2025-11-28'
        }
        return Response(order, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farmer_profiles(request):
    logger.info(f"Request: {request.method} {request.path}")
    # Allowing authenticated users to view profiles
    pass

    # Mock data for farmer profiles
    profiles = [
        {
            'id': 1,
            'name': 'রহিম ফার্মার',
            'rating': 4.5,
            'reviews': 12,
            'sales': 150,
            'specialties': ['ধান', 'গম'],
            'location': 'কুমিল্লা'
        },
        {
            'id': 2,
            'name': 'করিম ফার্মার',
            'rating': 4.8,
            'reviews': 8,
            'sales': 200,
            'specialties': ['পেঁয়াজ', 'আলু'],
            'location': 'রাজশাহী'
        }
    ]
    return Response(profiles)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_price_analysis(request):
    logger.info(f"Request: {request.method} {request.path}")
    pass

    # Mock data for price analysis
    analysis = {
        'ধান': {
            'average_price': 42.5,
            'farmer_prices': [40.0, 42.0, 45.0, 43.0],
            'trend': 'স্থিতিশীল'
        },
        'পেঁয়াজ': {
            'average_price': 75.0,
            'farmer_prices': [70.0, 75.0, 80.0, 78.0],
            'trend': 'ঊর্ধ্বমুখী'
        }
    }
    return Response(analysis)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buyer_inventory(request):
    logger.info(f"Request: {request.method} {request.path}")
    if request.user.role != 'buyer' and request.user.role != 'admin':
         return Response({'error': 'Only buyers can access inventory'}, status=status.HTTP_403_FORBIDDEN)

    # Mock data for buyer inventory
    inventory = {
        'currentStock': 500,
        'demand': 450,
        'suggestion': 'স্টক বাড়ান'
    }
    return Response(inventory)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_market_post(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    if user.role != 'farmer' and user.role != 'admin':
        return Response({'error': 'Only farmers or admins can create market posts'}, status=status.HTTP_403_FORBIDDEN)

    # Get data from request
    crop_name = request.data.get('crop_name', '').strip()
    quantity = request.data.get('quantity')
    price = request.data.get('price')
    location = request.data.get('location', '').strip()

    if not all([crop_name, quantity, price, location]):
        return Response({'error': 'crop_name, quantity, price, and location are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quantity = float(quantity)
        price = float(price)
    except ValueError:
        return Response({'error': 'quantity and price must be numbers'}, status=status.HTTP_400_BAD_REQUEST)

    # Create ProductPost
    product_post = ProductPost.objects.create(
        farmer=user,
        crop_name=crop_name,
        quantity=quantity,
        price=price,
        location=location,
        status='available'
    )

    return Response({
        'id': product_post.id,
        'farmer_id': user.id,
        'farmer_name': user.username,
        'crop_name': product_post.crop_name,
        'quantity': product_post.quantity,
        'price': product_post.price,
        'location': product_post.location,
        'created_at': product_post.date_posted,
        'status': product_post.status
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    data = {}

    if user.role == 'expert':
        # Expert Stats
        assigned_problems = Problem.objects.filter(assigned_expert=user)
        # If no explicit assignment logic yet, maybe all problems for now? 
        # But the model has assigned_expert. Let's assume it's used or we count all 'submitted'/'ai_completed' as pending for pool.
        # The user said "se koita farmer er problem show korche".
        # Let's count problems by status.
        
        # For now, let's just count all problems visible to expert
        # Or better, count problems where this expert has interacted or just global stats if they are a pool expert.
        # Let's return counts of all problems by status for the expert to see workload.
        
        total_problems = Problem.objects.count()
        resolved = Problem.objects.filter(status='resolved').count()
        pending = Problem.objects.filter(status__in=['submitted', 'ai_completed', 'expert_review']).count()
        
        data['expertStats'] = {
            'total': total_problems,
            'resolved': resolved,
            'pending': pending,
            'in_progress': total_problems - resolved - pending # rough estimate
        }
        
    elif user.role == 'farmer':
        # Farmer Stats (Existing PERT/Planner logic)
        latest_timeline = Timeline.objects.filter(farmer=user).order_by('-start_date').first()
        
        data['pertData'] = None
        data['plannerData'] = None
        
        if latest_timeline:
            crop = latest_timeline.crop
            
            # Get all timeline items for this crop and farmer
            timelines = Timeline.objects.filter(farmer=user, crop=crop).order_by('start_date')
            data['plannerData'] = TimelineSerializer(timelines, many=True).data
            
            # Calculate PERT data
            activities = Activity.objects.filter(crop=crop)
            total_expected = 0
            total_variance = 0
            pert_activities = []

            for activity in activities:
                expected = activity.expected_time()
                variance = activity.variance()
                total_expected += expected
                total_variance += variance
                pert_activities.append({
                    'activity': activity.name,
                    'optimistic': activity.optimistic_time,
                    'most_likely': activity.most_likely_time,
                    'pessimistic': activity.pessimistic_time,
                    'expected': round(expected, 2),
                    'variance': round(variance, 2),
                    'standard_deviation': round(variance ** 0.5, 2)
                })

            import math
            target_days = total_expected + 7
            z_score = (target_days - total_expected) / math.sqrt(total_variance) if total_variance > 0 else 0
            probability = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

            data['pertData'] = {
                'activities': pert_activities,
                'project_expected': round(total_expected, 2),
                'project_variance': round(total_variance, 2),
                'project_std_dev': round(math.sqrt(total_variance), 2),
                'completion_probability': round(probability * 100, 2)
            }
            
    else:
         return Response({'error': 'Unauthorized role'}, status=status.HTTP_403_FORBIDDEN)
        
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_item(request, item_id):
    logger.info(f"Request: {request.method} {request.path}")
    
    user = request.user
    # if user.role != 'buyer': # Relaxed for testing
    #     return Response({'error': 'Only buyers can buy items'}, status=status.HTTP_403_FORBIDDEN)

    try:
        product = ProductPost.objects.get(id=item_id)
    except ProductPost.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if product.status != 'available':
        return Response({'error': 'Product already sold'}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate total
    quantity_to_buy = product.quantity # For simplicity buying all
    total_price = quantity_to_buy * float(product.price)

    # Create Order
    order = Order.objects.create(
        buyer=user,
        product_post=product,
        quantity=quantity_to_buy,
        total_price=total_price,
        buyer_location=user.region or 'dhaka', # Default
        buyer_phone=user.phone or '01700000000', # Default
        status='confirmed' # Instantly confirm for demo
    )

    # Mark product as sold
    product.status = 'sold'
    product.buyer = user
    product.save()

    # Create Notification for Farmer
    from api.models import Notification # Import here to avoid circular
    Notification.objects.create(
        user=product.farmer,
        title='আপনার পণ্য বিক্রি হয়েছে!',
        message=f"{user.username} আপনার {product.crop_name} ({quantity_to_buy} kg) কিনেছেন।",
        notification_type='price_update',
        priority='high'
    )

    return Response({'message': 'Item purchased successfully', 'order_id': order.id, 'item_id': item_id}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_crop(request):
    logger.info(f"Request: {request.method} {request.path}")
    try:
        import joblib
        import pandas as pd
        import os
        
        # Load model and encoders
        model_path = os.path.join(settings.BASE_DIR, 'ml/saved_models')
        if not os.path.exists(model_path):
             return Response({'error': 'Model not trained yet'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        model = joblib.load(os.path.join(model_path, 'crop_model.pkl'))
        le_soil = joblib.load(os.path.join(model_path, 'le_soil.pkl'))
        le_season = joblib.load(os.path.join(model_path, 'le_season.pkl'))
        le_region = joblib.load(os.path.join(model_path, 'le_region.pkl'))
        le_crop = joblib.load(os.path.join(model_path, 'le_crop.pkl'))

        data = request.data
        soil_type = data.get('soil_type')
        season = data.get('season')
        region = data.get('region')

        if not all([soil_type, season, region]):
            return Response({'error': 'Missing fields: soil_type, season, region'}, status=status.HTTP_400_BAD_REQUEST)

        # Encode inputs
        try:
            soil_enc = le_soil.transform([soil_type])[0]
            season_enc = le_season.transform([season])[0]
            region_enc = le_region.transform([region])[0]
        except ValueError as e:
             return Response({'error': f'Invalid input values: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Predict
        prediction_enc = model.predict([[soil_enc, season_enc, region_enc]])[0]
        prediction = le_crop.inverse_transform([prediction_enc])[0]
        
        # Confidence
        proba = model.predict_proba([[soil_enc, season_enc, region_enc]])
        confidence = max(proba[0])

        return Response({
            'recommended_crop': prediction,
            'confidence': round(confidence, 2),
            'inputs': {
                'soil_type': soil_type,
                'season': season,
                'region': region
            }
        })

    except Exception as e:
        logger.error(f"ML Prediction Error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
