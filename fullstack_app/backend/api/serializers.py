from rest_framework import serializers
from .models import User, Post, Comment, Problem, Reply, Crop, ChatMessage, WeatherData, Activity, Timeline, Progress, MarketPrice, ExpenseCalculation, Notification, ProblemSolution, CropRecommendation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'phone']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'image', 'created_at', 'author', 'comments']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

    def get_comments(self, obj):
        comments = obj.comments.all().order_by('-created_at')
        return CommentSerializer(comments, many=True, context=self.context).data

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_at', 'author']

class ProblemSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)
    assigned_expert = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    solution = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = ['id', 'title', 'description', 'image', 'video', 'created_at', 'farmer', 'tracking_id', 'status', 'ai_solution', 'expert_solution', 'assigned_expert', 'solution_date', 'crop_type', 'problem_type', 'start_date', 'severity_level', 'replies', 'solution']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

    def get_video(self, obj):
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
        return None

    def get_replies(self, obj):
        replies = obj.replies.all().order_by('-created_at')
        return ReplySerializer(replies, many=True, context=self.context).data

    def get_solution(self, obj):
        try:
            solution = obj.solution
            return ProblemSolutionSerializer(solution, context=self.context).data
        except:
            return None

class ReplySerializer(serializers.ModelSerializer):
    admin = UserSerializer(read_only=True)

    class Meta:
        model = Reply
        fields = ['id', 'content', 'created_at', 'admin']

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = ['id', 'name', 'season']

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # phone or secret code

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'message', 'response', 'image', 'created_at']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = ['date', 'temperature', 'humidity', 'rainfall']

class ActivitySerializer(serializers.ModelSerializer):
    dependencies = serializers.SerializerMethodField()
    expected_time = serializers.SerializerMethodField()
    variance = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ['id', 'crop', 'name', 'duration_days', 'dependencies', 'optimistic_time', 'most_likely_time', 'pessimistic_time', 'order', 'expected_time', 'variance']

    def get_dependencies(self, obj):
        return [dep.id for dep in obj.dependencies.all()]

    def get_expected_time(self, obj):
        return round(obj.expected_time(), 2)

    def get_variance(self, obj):
        return round(obj.variance(), 2)

class TimelineSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer(read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Timeline
        fields = ['id', 'farmer', 'crop', 'activity', 'start_date', 'end_date', 'is_critical', 'weather_delay_days', 'progress']

    def get_progress(self, obj):
        try:
            progress = obj.progress
            return {
                'completed_percentage': progress.completed_percentage,
                'last_updated': progress.last_updated,
                'notes': progress.notes
            }
        except:
            return None

class ProgressSerializer(serializers.ModelSerializer):
    timeline = TimelineSerializer(read_only=True)

    class Meta:
        model = Progress
        fields = ['id', 'timeline', 'completed_percentage', 'last_updated', 'notes']

class MarketPriceSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = MarketPrice
        fields = ['id', 'crop_name', 'market_name', 'district', 'price_per_kg', 'date', 'source', 'updated_by_username']
        read_only_fields = ['id', 'updated_by_username']

class ExpenseCalculationSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)
    crop = CropSerializer(read_only=True)
    crop_id = serializers.PrimaryKeyRelatedField(
        queryset=Crop.objects.all(), source='crop', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ExpenseCalculation
        fields = [
            'id', 'farmer', 'crop', 'crop_id', 'seed_cost', 'fertilizer_cost', 'labour_cost', 'other_cost',
            'area', 'expected_yield_per_area', 'market_price_per_kg', 'actual_yield', 'created_at',
            'total_cost', 'expected_total_yield', 'expected_revenue', 'expected_profit_loss', 'expected_profit_margin',
            'actual_revenue', 'actual_profit_loss', 'actual_profit_margin'
        ]
        read_only_fields = [
            'id', 'farmer', 'created_at', 'total_cost', 'expected_total_yield', 'expected_revenue',
            'expected_profit_loss', 'expected_profit_margin', 'actual_revenue', 'actual_profit_loss', 'actual_profit_margin'
        ]

    def validate(self, data):
        if (data.get('area') or 0) <= 0:
            raise serializers.ValidationError("Area must be greater than 0.")
        if (data.get('expected_yield_per_area') or 0) <= 0:
            raise serializers.ValidationError("Expected yield per area must be greater than 0.")
        if (data.get('market_price_per_kg') or 0) <= 0:
            raise serializers.ValidationError("Market price per kg must be greater than 0.")
        if data.get('actual_yield') and (data.get('actual_yield') or 0) < 0:
            raise serializers.ValidationError("Actual yield cannot be negative.")
        return data

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'is_read', 'priority', 'notification_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class ProblemSolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemSolution
        fields = ['id', 'ai_analysis', 'expert_analysis', 'recommended_treatment', 'preventive_measures', 'confidence_score', 'created_at', 'updated_at']

class CropRecommendationSerializer(serializers.ModelSerializer):
    recommended_crop = CropSerializer(read_only=True)

    class Meta:
        model = CropRecommendation
        fields = ['id', 'soil_type', 'season', 'region', 'recommended_crop', 'expected_yield', 'tips', 'confidence', 'created_at']
        read_only_fields = ['id', 'created_at']
