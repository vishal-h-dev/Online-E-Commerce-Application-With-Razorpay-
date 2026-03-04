from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Seed store safely with all products"

    def handle(self, *args, **kwargs):

        from store.models import Category, Brand, Product

        media_path = os.path.join(settings.MEDIA_ROOT, "products")

        # -------- Categories --------
        def get_category(slug):
            return Category.objects.get_or_create(
                slug=slug,
                defaults={"name": slug}
            )[0]

        smartphones = get_category("smartphones")
        laptops = get_category("laptops")
        gaming = get_category("gaming")
        audio = get_category("audio")

        # -------- Brands --------
        def get_brand(name):
            return Brand.objects.get_or_create(
                slug=name,
                defaults={"name": name}
            )[0]

        apple = get_brand("apple")
        samsung = get_brand("samsung")
        google = get_brand("google")
        motorola = get_brand("motorola")
        hp = get_brand("hp")
        lenovo = get_brand("lenovo")
        asus = get_brand("asus")
        microsoft = get_brand("microsoft")
        sony = get_brand("sony")
        jbl = get_brand("jbl")
        skullcandy = get_brand("skullcandy")
        valve = get_brand("valve")
        msi = get_brand("msi")

        # -------- Product Creator --------
        def create_product(name, brand, category, type_, desc, cost, stock, image_name):

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "brand": brand,
                    "category": category,
                    "type_of_product": type_,
                    "description": desc,
                    "cost": cost,
                    "stock": stock,
                    "available": True,
                }
            )

            if created:
                image_path = os.path.join(media_path, image_name)

                if os.path.exists(image_path):
                    with open(image_path, "rb") as img:
                        product.image.save(image_name, File(img), save=True)
                else:
                    print(f"Missing image: {image_path}")

        # -------- AUDIO --------
        create_product("airpods pro 3", apple, audio, "earbuds",
                       "premium anc earbuds with adaptive spatial audio.",
                       25999, 40, "airpods.png")

        create_product("jbl live beam 3", jbl, audio, "earbuds",
                       "hi-res true wireless earbuds with smart case.",
                       14999, 35, "jbl_livebeam.png")

        create_product("skullcandy dime evo", skullcandy, audio, "earbuds",
                       "compact wireless earbuds with rapid charge.",
                       5999, 50, "skullcandy.png")

        # -------- GAMING --------
        create_product("steam deck oled 1tb", valve, gaming, "handheld console",
                       "portable gaming pc with hdr oled display.",
                       69999, 15, "steamdeck.png")

        create_product("ps5", sony, gaming, "console",
                       "next-gen console with ultra-fast ssd.",
                       54999, 20, "ps5.png")

        create_product("msi handheld gaming", msi, gaming, "handheld console",
                       "high-performance portable gaming console.",
                       79999, 12, "msi_handheld.png")

        # -------- SMARTPHONES --------
        create_product("iphone 17 pro", apple, smartphones, "smartphone",
                       "flagship iphone with advanced ai camera.",
                       139999, 25, "iphone17.png")

        create_product("samsung galaxy s26 ultra", samsung, smartphones, "smartphone",
                       "200mp camera system with snapdragon elite.",
                       129999, 20, "s26_ultra.png")

        create_product("google pixel 10 5g", google, smartphones, "smartphone",
                       "pure android with computational photography.",
                       89999, 18, "pixel10.png")

        create_product("motorola razr 60 ultra", motorola, smartphones, "smartphone",
                       "premium foldable with 165hz display.",
                       99999, 14, "razr60.png")

        create_product("samsung galaxy z fold7", samsung, smartphones, "smartphone",
                       "ultra-sleek foldable with galaxy ai.",
                       149999, 10, "zfold7.png")

        # -------- LAPTOPS --------
        create_product("macbook pro m5", apple, laptops, "laptop",
                       "14-inch liquid retina xdr display powered by m5 chip.",
                       199999, 10, "macbook.png")

        create_product("hp victus i7 rtx 5060", hp, laptops, "laptop",
                       "13th gen i7 gaming laptop with rtx graphics.",
                       124999, 15, "hp_victus.png")

        create_product("thinkpad e14", lenovo, laptops, "laptop",
                       "business-class laptop with durable build.",
                       89999, 18, "thinkpad.png")

        create_product("asus zenbook 14", asus, laptops, "laptop",
                       "lightweight oled laptop powered by ryzen ai.",
                       94999, 16, "zenbook.png")

        create_product("surface pro", microsoft, laptops, "2-in-1",
                       "versatile 2-in-1 with touchscreen and detachable keyboard.",
                       109999, 12, "surfacepro.png")

        self.stdout.write(self.style.SUCCESS("All products seeded safely"))