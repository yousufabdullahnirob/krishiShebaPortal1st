# New models for enhanced role-based features

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('inactive', 'Inactive'),
    ]
    farmer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    harvest_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.farmer.username}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    buyer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='orders')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    delivery_address = models.TextField(blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity_kg * self.product.price_per_kg
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"

class Article(models.Model):
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ForumPost(models.Model):
    author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='forum/', blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ForumReply(models.Model):
    post = models.ForeignKey('ForumPost', on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey('User', on_delete=models.CASCADE)
    content = models.TextField()
    is_expert_answer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.author.username} on {self.post.title}"

class ExpertRating(models.Model):
    expert = models.ForeignKey('User', on_delete=models.CASCADE, related_name='ratings')
    farmer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='given_ratings')
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for {self.expert.username} by {self.farmer.username}"

class CropReminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ('fertilizer', 'Fertilizer Application'),
        ('irrigation', 'Irrigation'),
        ('pesticide', 'Pesticide Application'),
        ('harvest', 'Harvest Time'),
        ('planting', 'Planting Time'),
    ]
    farmer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='reminders')
    crop = models.ForeignKey('Crop', on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reminder_type} reminder for {self.farmer.username}"

class WeatherAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('storm', 'Storm Warning'),
        ('flood', 'Flood Warning'),
        ('drought', 'Drought Warning'),
        ('heat', 'Heat Wave'),
        ('cold', 'Cold Wave'),
        ('rain', 'Heavy Rain'),
    ]
    region = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alert_type} alert for {self.region}"

class LedgerEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    farmer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='ledger_entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    category = models.CharField(max_length=100, help_text="e.g., Fertilizer, Seeds, Sales, etc.")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    related_crop = models.ForeignKey('Crop', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entry_type}: {self.amount} by {self.farmer.username}"

class RequestCrop(models.Model):
    buyer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='crop_requests')
    crop_name = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    max_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)
    delivery_location = models.CharField(max_length=100)
    delivery_date = models.DateField()
    is_fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request for {self.crop_name} by {self.buyer.username}"
