from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('expert', 'Expert'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')
    phone = models.CharField(max_length=11, unique=True, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Dhaka, Rajshahi, Cumilla")

    def clean(self):
        if self.phone and len(self.phone) != 11:
            raise ValidationError('Phone number must be exactly 11 digits.')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='api_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='api_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    is_active = models.BooleanField(default=True, help_text="Indicates if the post is currently active/relevant")

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

class Problem(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('ai_processing', 'AI Processing'),
        ('ai_completed', 'AI Completed'),
        ('expert_review', 'Expert Review'),
        ('expert_completed', 'Expert Completed'),
        ('resolved', 'Resolved'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='problems/', blank=True, null=True)
    video = models.FileField(upload_to='problem_videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problems')

    # Agri-Doctor specific fields
    tracking_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    ai_solution = models.TextField(blank=True, null=True)
    expert_solution = models.TextField(blank=True, null=True)
    assigned_expert = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_problems')
    solution_date = models.DateTimeField(null=True, blank=True)
    crop_type = models.CharField(max_length=100, blank=True, null=True)
    problem_type = models.CharField(max_length=100, blank=True, null=True, choices=[
        ('পোকা', 'পোকা'),
        ('রোগ', 'রোগ'),
        ('সারের অভাব', 'সারের অভাব'),
        ('আবহাওয়া', 'আবহাওয়া'),
        ('মাটি', 'মাটি'),
        ('অন্যান্য', 'অন্যান্য'),
    ])
    start_date = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('আজ', 'আজ'),
        ('গতকাল', 'গতকাল'),
        ('২-৩ দিন আগে', '২-৩ দিন আগে'),
        ('১ সপ্তাহ আগে', '১ সপ্তাহ আগে'),
        ('২ সপ্তাহ আগে', '২ সপ্তাহ আগে'),
        ('১ মাস আগে', '১ মাস আগে'),
        ('আরও আগে', 'আরও আগে'),
    ])
    severity_level = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            import uuid
            self.tracking_id = f"AGRI-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_id} - {self.title}"

class Reply(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='replies')
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.admin.username} on {self.problem.title}"

class Crop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    season = models.CharField(max_length=50, help_text="e.g., Summer, Winter, Monsoon")

    def __str__(self):
        return f"{self.name} ({self.season})"

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    symptoms = models.TextField()
    treatment = models.TextField()
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='diseases/', blank=True, null=True)

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat by {self.user.username} at {self.created_at}"

class WeatherData(models.Model):
    date = models.DateField(unique=True)
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.FloatField(help_text="Humidity percentage")
    rainfall = models.FloatField(default=0, help_text="Rainfall in mm")

    def __str__(self):
        return f"Weather on {self.date}: {self.temperature}°C, {self.humidity}%, {self.rainfall}mm"

class Activity(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=100, help_text="e.g., Land Prep, Seed Planting")
    duration_days = models.IntegerField(help_text="Estimated duration in days")
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, help_text="Activities that must be completed before this one")
    optimistic_time = models.IntegerField(help_text="Optimistic duration (O)")
    most_likely_time = models.IntegerField(help_text="Most likely duration (M)")
    pessimistic_time = models.IntegerField(help_text="Pessimistic duration (P)")
    order = models.IntegerField(default=0, help_text="Order in the process")

    def expected_time(self):
        return (self.optimistic_time + 4 * self.most_likely_time + self.pessimistic_time) / 6

    def variance(self):
        return ((self.pessimistic_time - self.optimistic_time) / 6) ** 2

    def __str__(self):
        return f"{self.crop.name} - {self.name}"

    class Meta:
        ordering = ['crop', 'order']

class Timeline(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timelines')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_critical = models.BooleanField(default=False)
    weather_delay_days = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.farmer.username} - {self.activity.name} ({self.start_date} to {self.end_date})"

class Progress(models.Model):
    timeline = models.OneToOneField(Timeline, on_delete=models.CASCADE, related_name='progress')
    completed_percentage = models.IntegerField(default=0, help_text="0-100")
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.timeline.activity.name} - {self.completed_percentage}%"

class MarketPrice(models.Model):
    crop_name = models.CharField(max_length=100, help_text="ফসলের নাম")
    market_name = models.CharField(max_length=100, help_text="বাজারের নাম")
    district = models.CharField(max_length=100, help_text="জেলা")
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="প্রতি kg এর দাম (BDT)")
    date = models.DateField(auto_now_add=True, help_text="তারিখ")
    source = models.CharField(max_length=50, default='manual', help_text="উৎস (manual, govt_api)")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_updated_prices')

    def __str__(self):
        return f"{self.crop_name} - {self.market_name}, {self.district}: {self.price_per_kg} BDT/kg ({self.date})"

class ExpenseCalculation(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_calculations')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True, related_name='expense_calculations')
    seed_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Seed cost in BDT")
    fertilizer_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fertilizer cost in BDT")
    labour_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Labour cost in BDT")
    other_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Other costs in BDT")
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in acres")
    expected_yield_per_area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Expected yield per area in kg/acre")
    market_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Market price per kg in BDT")
    actual_yield = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Actual yield in kg")
    created_at = models.DateTimeField(auto_now_add=True)

    # Calculated fields for expected
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    expected_total_yield = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    expected_revenue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    expected_profit_loss = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    expected_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Expected profit margin in %")

    # Calculated fields for actual
    actual_revenue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    actual_profit_loss = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    actual_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Actual profit margin in %")

    def save(self, *args, **kwargs):
        # Ensure costs are treated as 0 if None
        seed = self.seed_cost or 0
        fertilizer = self.fertilizer_cost or 0
        labour = self.labour_cost or 0
        other = self.other_cost or 0
        
        self.total_cost = seed + fertilizer + labour + other
        
        # Ensure yield calculations are safe
        yield_per_area = self.expected_yield_per_area or 0
        area = self.area or 0
        self.expected_total_yield = yield_per_area * area
        
        price = self.market_price_per_kg or 0
        self.expected_revenue = self.expected_total_yield * price
        
        self.expected_profit_loss = self.expected_revenue - self.total_cost
        
        if self.expected_revenue > 0:
            self.expected_profit_loss = self.expected_revenue - self.total_cost # Recalculate to be sure
            self.expected_profit_margin = (self.expected_profit_loss / self.expected_revenue) * 100
        else:
            self.expected_profit_margin = 0

        if self.actual_yield:
            self.actual_revenue = self.actual_yield * price
            self.actual_profit_loss = self.actual_revenue - self.total_cost
            if self.actual_revenue > 0:
                self.actual_profit_margin = (self.actual_profit_loss / self.actual_revenue) * 100
            else:
                 self.actual_profit_margin = 0


        super().save(*args, **kwargs)

    def __str__(self):
        return f"Calculation by {self.farmer.username} for {self.crop.name if self.crop else 'Unknown Crop'} - Expected Profit: {self.expected_profit_loss} BDT"

class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    TYPE_CHOICES = [
        ('admin_reply', 'Admin Reply'),
        ('weather_alert', 'Weather Alert'),
        ('price_update', 'Price Update'),
        ('system_reminder', 'System Reminder'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system_reminder')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

class ProblemSolution(models.Model):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='solution')
    ai_analysis = models.TextField(blank=True, null=True)
    expert_analysis = models.TextField(blank=True, null=True)
    recommended_treatment = models.TextField(blank=True, null=True)
    preventive_measures = models.TextField(blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="AI confidence score 0-1")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Solution for {self.problem.tracking_id}"

class CropRecommendation(models.Model):
    SOIL_CHOICES = [
        ('clay', 'Clay'),
        ('loam', 'Loam'),
        ('sandy', 'Sandy'),
        ('silt', 'Silt'),
    ]
    SEASON_CHOICES = [
        ('kharif', 'Kharif'),
        ('rabi', 'Rabi'),
        ('zaid', 'Zaid'),
    ]
    soil_type = models.CharField(max_length=10, choices=SOIL_CHOICES)
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)
    region = models.CharField(max_length=100, blank=True, null=True)
    recommended_crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    expected_yield = models.DecimalField(max_digits=10, decimal_places=2, help_text="Expected yield in tons/acre")
    tips = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Confidence level 0-1")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation: {self.recommended_crop.name} for {self.soil_type} soil in {self.season} season"

class OTPVerification(models.Model):
    identifier = models.CharField(max_length=255)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_expired(self):
        from django.utils import timezone
        import datetime
        return timezone.now() > self.created_at + datetime.timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.identifier}: {self.otp_code}"

class KnowledgeBase(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_items')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
