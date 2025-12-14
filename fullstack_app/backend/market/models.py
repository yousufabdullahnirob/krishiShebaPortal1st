from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductPost(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_posts')
    crop_name = models.CharField(max_length=100, help_text="ফসলের নাম (ধান, গম, পেঁয়াজ, আলু...)")
    quantity = models.FloatField(help_text="পরিমাণ (kg বা ton)")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="প্রতি kg এর দাম (BDT)")
    location = models.CharField(max_length=100, help_text="বাজার/এলাকা")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    date_posted = models.DateTimeField(auto_now_add=True)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_posts')

    def __str__(self):
        return f"{self.crop_name} - {self.quantity}kg by {self.farmer.username} at {self.location}"

class MarketPrice(models.Model):
    crop_name = models.CharField(max_length=100, help_text="ফসলের নাম")
    market_name = models.CharField(max_length=100, help_text="বাজারের নাম")
    district = models.CharField(max_length=100, help_text="জেলা")
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="প্রতি kg এর দাম (BDT)")
    date = models.DateField(auto_now_add=True, help_text="তারিখ")
    source = models.CharField(max_length=50, default='manual', help_text="উৎস (manual, govt_api)")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_prices')

    def __str__(self):
        return f"{self.crop_name} - {self.market_name}, {self.district}: {self.price_per_kg} BDT/kg ({self.date})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product_post = models.ForeignKey(ProductPost, on_delete=models.CASCADE, related_name='orders')
    quantity = models.FloatField(help_text="Quantity ordered (kg)")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total calculated price")
    buyer_location = models.CharField(max_length=255, help_text="Delivery location")
    buyer_phone = models.CharField(max_length=20, help_text="Contact number")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username} for {self.product_post.crop_name}"
