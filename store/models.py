from django.db import models
from django.contrib.auth.models import User

# Customer Profile with multiple phone numbers and addresses
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class PhoneNumber(models.Model):
    customer = models.ForeignKey(CustomerProfile, related_name='phone_numbers', on_delete=models.CASCADE)
    number = models.CharField(max_length=20)

    def __str__(self):
        return self.number

class Address(models.Model):
    customer = models.ForeignKey(CustomerProfile, related_name='addresses', on_delete=models.CASCADE)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_line}, {self.city}"

# Category and Brand
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

# Product, with reviews
class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True)
    type_of_product = models.CharField(max_length=100)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum([r.stars for r in reviews]) / reviews.count(), 2)
        return None

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    customer = models.ForeignKey(CustomerProfile, related_name='reviews', on_delete=models.CASCADE)
    review_text = models.TextField()
    stars = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stars} stars by {self.customer}"

# Cart and CartItem
class Cart(models.Model):
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart for {self.customer}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of adding to cart

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

# Order and OrderItem
class Order(models.Model):
    customer = models.ForeignKey(CustomerProfile, related_name='orders', on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    payment_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')])
    delivery_status = models.CharField(max_length=20, choices=[('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered')])
    date_of_purchase = models.DateTimeField(auto_now_add=True)
    date_of_delivery = models.DateTimeField(null=True, blank=True)
    payment_order_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted product'}"

class Wishlist(models.Model):
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='wishlist')

    def __str__(self):
        return f"Wishlist of {self.customer}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f"{self.product.name} in wishlist"

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, help_text="Enter percentage (e.g., 10 for 10%)")
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return f"{self.code} ({self.discount}%)"
