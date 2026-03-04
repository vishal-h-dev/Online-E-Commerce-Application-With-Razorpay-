from django.core.management.base import BaseCommand
from store.models import Category, Brand, Product, Coupon
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Seed database with initial store data"

    def handle(self, *args, **kwargs):

        if Category.objects.exists():
            self.stdout.write(self.style.WARNING("Database already seeded."))
            return

        # Create Categories
        electronics = Category.objects.create(name="Electronics")
        audio = Category.objects.create(name="Audio")
        accessories = Category.objects.create(name="Accessories")

        # Create Brands
        apple = Brand.objects.create(name="Apple")
        samsung = Brand.objects.create(name="Samsung")
        sony = Brand.objects.create(name="Sony")

        # Create Products
        Product.objects.create(
            name="iPhone 15",
            category=electronics,
            brand=apple,
            price=79999,
            stock=15,
            description="Latest Apple flagship phone"
        )

        Product.objects.create(
            name="Samsung Galaxy S24",
            category=electronics,
            brand=samsung,
            price=74999,
            stock=20,
            description="Premium Samsung smartphone"
        )

        Product.objects.create(
            name="Sony WH-1000XM5",
            category=audio,
            brand=sony,
            price=29999,
            stock=10,
            description="Industry-leading noise cancelling headphones"
        )

        # Create Coupon
        Coupon.objects.create(
            code="WELCOME10",
            discount=10,
            active=True,
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30)
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
