import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import F, Q, Sum
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .forms import CouponApplyForm
from .models import (
    Address, Cart, CartItem, Coupon, CustomerProfile,
    Order, OrderItem, PhoneNumber
)
import razorpay

from .forms import (
    UserRegistrationForm, CustomerProfileForm, PhoneNumberForm,
    AddressForm, CouponApplyForm
)
from .models import (
    User, CustomerProfile, Product, Category, Brand, Cart, CartItem,
    Wishlist, WishlistItem, Order, OrderItem, Address, PhoneNumber, Coupon
)
from django.forms import ModelChoiceField, IntegerField, HiddenInput, modelformset_factory

import razorpay

# --- Authentication Views ---

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            profile = CustomerProfile.objects.get_or_create(
                user=user,
                email=user.email,
                first_name='',
                last_name='',
            )
            Cart.objects.create(customer=profile)
            Wishlist.objects.create(customer=profile)
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'store/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- Product and Catalog Views ---

@login_required
def home(request):
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).order_by('-id')[:24]
    return render(request, 'store/home.html', {
        'categories': categories,
        'products': products,
    })

@login_required
def category_products(request, slug):
    categories = Category.objects.all()
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)
    return render(request, 'store/home.html', {
        'categories': categories,
        'products': products,
        'current_category': category,
    })

@login_required
def product_search(request):
    query = request.GET.get('q', '')
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'store/home.html', {
        'categories': categories,
        'products': products,
        'search_query': query,
    })

# --- Cart Views ---

@login_required
def cart(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_items = cart.items.select_related('product')
    cart_total = sum(item.product.cost * item.quantity for item in cart_items)
    for item in cart_items:
        item.total_price = item.product.cost * item.quantity
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
    })

@login_required
def add_to_cart(request, product_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    product = get_object_or_404(Product, pk=product_id, available=True)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product,
                                                        defaults={'price': product.cost})
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Quantity updated for {product.name}.")
    else:
        messages.success(request, f"Added {product.name} to cart.")
    return redirect('cart')

@login_required
def update_cart_quantity(request, item_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart = get_object_or_404(Cart, customer=customer)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "increase":
            cart_item.quantity += 1
            cart_item.save()
        elif action == "decrease":
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
        messages.success(request, "Cart updated.")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart = get_object_or_404(Cart, customer=customer)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if request.method == "POST":
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def save_for_later(request, item_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart = get_object_or_404(Cart, customer=customer)
    wishlist, _ = Wishlist.objects.get_or_create(customer=customer)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product = cart_item.product
    # Add to wishlist if not already present
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    cart_item.delete()
    messages.success(request, f"{product.name} saved for later.")
    return redirect('cart')
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    reviews = product.reviews.select_related('customer__user').order_by('-id')
    avg_rating = product.average_rating() or 0
    review_count = reviews.count()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
    })
# --- Wishlist Views ---

@login_required
def wishlist(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    wishlist, _ = Wishlist.objects.get_or_create(customer=customer)
    wishlist_items = wishlist.items.select_related('product')
    return render(request, 'store/wishlist.html', {
        'wishlist_items': wishlist_items
    })

@login_required
def add_to_wishlist(request, product_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    wishlist, _ = Wishlist.objects.get_or_create(customer=customer)
    product = get_object_or_404(Product, pk=product_id, available=True)
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    messages.success(request, f"{product.name} added to wishlist.")
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, item_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    wishlist = get_object_or_404(Wishlist, customer=customer)
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
    wishlist_item.delete()
    messages.success(request, "Item removed from wishlist.")
    return redirect('wishlist')

@login_required
def move_to_cart(request, item_id):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    wishlist = get_object_or_404(Wishlist, customer=customer)
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
    product = wishlist_item.product
    # Add to cart
    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'price': product.cost})
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    wishlist_item.delete()
    messages.success(request, f"{product.name} moved to cart.")
    return redirect('cart')

# --- Orders ---

@login_required
def orders(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-date_of_purchase').prefetch_related('items__product')
    return render(request, 'store/orders.html', {
        'orders': orders
    })

# --- Profile ---



@login_required
def profile(request):
    customer, _ = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "email": request.user.email,
            "first_name": "",
            "last_name": "",
        }
    )

    # Profile edit
    if request.method == 'POST' and 'profile_submit' in request.POST:
        profile_form = CustomerProfileForm(request.POST, instance=customer)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
    else:
        profile_form = CustomerProfileForm(instance=customer)

    # PhoneNumber Add
    if request.method == 'POST' and 'add_phone' in request.POST:
        phone_form = PhoneNumberForm(request.POST)
        if phone_form.is_valid():
            phone = phone_form.save(commit=False)
            phone.customer = customer
            phone.save()
            messages.success(request, "Phone number added.")
            return redirect('profile')
    else:
        phone_form = PhoneNumberForm()

    # Address Add
    if request.method == 'POST' and 'add_address' in request.POST:
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.customer = customer
            address.save()
            messages.success(request, "Address added.")
            return redirect('profile')
    else:
        address_form = AddressForm()

    # Delete phone
    if request.method == 'POST' and 'delete_phone' in request.POST:
        phone_id = request.POST.get('delete_phone')
        PhoneNumber.objects.filter(id=phone_id, customer=customer).delete()
        messages.success(request, "Phone number deleted.")
        return redirect('profile')

    # Delete address
    if request.method == 'POST' and 'delete_address' in request.POST:
        address_id = request.POST.get('delete_address')
        Address.objects.filter(id=address_id, customer=customer).delete()
        messages.success(request, "Address deleted.")
        return redirect('profile')

    phones = customer.phone_numbers.all()
    addresses = customer.addresses.all()
    cart = getattr(customer, 'cart', None)
    cart_items = cart.items.select_related('product') if cart else []
    orders = customer.orders.all().order_by('-date_of_purchase')[:10]

    return render(request, 'store/profile.html', {
        'customer': customer,
        'profile_form': profile_form,
        'phones': phones,
        'addresses': addresses,
        'phone_form': phone_form,
        'address_form': address_form,
        'cart_items': cart_items,
        'orders': orders,
    })
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def checkout(request):
    customer = request.user.customerprofile
    cart = getattr(customer, 'cart', None)
    cart_items = cart.items.select_related('product') if cart else []
    key_id = settings.RAZORPAY_KEY_ID

    # For address and phone selection
    addresses = customer.addresses.all()
    phones = customer.phone_numbers.all()
    for item in cart_items:
        item.subtotal = item.product.cost * item.quantity
    total_amount = sum(item.subtotal for item in cart_items)
    coupon_discount = 0
    coupon_applied = None

    # Coupon logic
    if request.method == "POST" and "apply_coupon" in request.POST:
        coupon_form = CouponApplyForm(request.POST)
        if coupon_form.is_valid():
            code = coupon_form.cleaned_data['code']
            now = timezone.now()
            try:
                coupon = Coupon.objects.get(
                    code__iexact=code,
                    active=True,
                    valid_from__lte=now,
                    valid_to__gte=now
                )
                coupon_discount = (total_amount * coupon.discount) / 100
                coupon_applied = coupon
                request.session['applied_coupon'] = coupon.code
                messages.success(request, f"Coupon applied: {coupon.code} ({coupon.discount}% OFF)")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid or expired coupon.")
    else:
        coupon_form = CouponApplyForm()
        code = request.session.get('applied_coupon')
        if code:
            now = timezone.now()
            try:
                coupon = Coupon.objects.get(
                    code__iexact=code,
                    active=True,
                    valid_from__lte=now,
                    valid_to__gte=now
                )
                coupon_discount = (total_amount * coupon.discount) / 100
                coupon_applied = coupon
            except Coupon.DoesNotExist:
                request.session.pop('applied_coupon')

    total_after_discount = total_amount - coupon_discount

    # Always create a new payment/order for Razorpay
    payment = client.order.create({
        "amount" : int(total_after_discount * 100),
        "currency" : "INR",
        "payment_capture": 1,
    })
    order_id = payment['id']

    # Update address/phone/quantities if POST and not coupon apply
    if request.method == "POST" and "apply_coupon" not in request.POST:
        address_id = request.POST.get("address")
        phone_id = request.POST.get("phone")
        quantities = {k.split('-')[-1]: v for k, v in request.POST.items() if k.startswith('quantity-')}
        for item in cart_items:
            q = int(quantities.get(str(item.id), item.quantity))
            if q > 0:
                item.quantity = q
                item.save()
            else:
                item.delete()
        request.session['checkout_address_id'] = address_id
        request.session['checkout_phone_id'] = phone_id
        messages.success(request, "Checkout details updated! Continue to payment.")

    selected_address_id = request.session.get('checkout_address_id')
    selected_phone_id = request.session.get('checkout_phone_id')

    return render(request, 'store/checkout.html', {
        'customer': customer,
        'cart_items': cart_items,
        'addresses': addresses,
        'phones': phones,
        'selected_address_id': selected_address_id,
        'selected_phone_id': selected_phone_id,
        'coupon_form': coupon_form,
        'coupon_applied': coupon_applied,
        'coupon_discount': coupon_discount,
        'total_amount': total_amount,
        'total_after_discount': total_after_discount,
        'payment': payment,
        'order_id': order_id,
        'key_id': key_id,
    })

@login_required
def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id, customer=request.user.customerprofile)
    return render(request, 'store/order_confirmation.html', {'order': order})
@login_required
def remove_coupon(request):
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
        messages.info(request, "Coupon removed.")
    return redirect('checkout')
# ------- Payment Section ---------

@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        data = json.loads(request.body.decode())
        payment_id = data.get("razorpay_payment_id")
        order_id = data.get("razorpay_order_id")
        signature = data.get("razorpay_signature")
        address_id = request.session.get('checkout_address_id')
        phone_id = request.session.get('checkout_phone_id')

        params_dict = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            print("Signature verification failed:", e)
            return JsonResponse({"success": False, "error": "Payment Signature Verification Failed"}, status=400)

        # Fetch payment and check status
        try:
            payment_obj = client.payment.fetch(payment_id)
            print("Fetched payment_obj:", payment_obj)
        except Exception as e:
            print("Failed to fetch payment:", e)
            return JsonResponse({"success": False, "error": "Failed to fetch payment: %s" % str(e)}, status=400)

        if payment_obj.get("status") != "captured":
            print("Payment not captured:", payment_obj.get("status"))
            return JsonResponse({"success": False, "error": f"Payment status not captured (got {payment_obj.get('status')})"}, status=400)

        customer = request.user.customerprofile
        cart = getattr(customer, 'cart', None)
        cart_items = cart.items.select_related('product') if cart else []
        address = Address.objects.filter(id=address_id, customer=customer).first()
        print("SESSION address_id:", address_id)
        print("SESSION phone_id:", phone_id)
        print("Customer:", customer)
        print("Cart:", cart)
        print("Cart Items:", list(cart_items))
        print("Addresses:", list(Address.objects.filter(customer=customer)))
        print("Selected address obj:", address)

        if not cart_items or not address:
            print("No cart items or address")
            return JsonResponse({"success": False, "error": "Invalid cart or address."}, status=400)

        # Prevent duplicate order creation
        if Order.objects.filter(payment_order_id=order_id).exists():
            print("Order already exists for this payment_order_id")
            order = Order.objects.get(payment_order_id=order_id)
            return JsonResponse({"success": True, "order_id": order.id})

        order = Order.objects.create(
            customer=customer,
            address=address,
            payment_status='paid',
            delivery_status='processing',
            payment_order_id=order_id
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.cost
            )
        cart.items.all().delete()
        print("Order created successfully, order_id:", order.id)
        return JsonResponse({"success": True, "order_id": order.id})

    return HttpResponseBadRequest("Invalid request")
from django.contrib import messages

@login_required
def orders(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-date_of_purchase').prefetch_related('items__product')
    if request.GET.get("payment") == "success":
        messages.success(request, "Payment successful! Your order has been placed.")
    return render(request, 'store/orders.html', {'orders': orders})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Review
from .forms import ReviewForm

@login_required
def product_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    customer = request.user.customerprofile
    # Show recent reviews for this product
    reviews = product.reviews.select_related('customer__user').order_by('-id')
    # Check if the customer already left a review (optional)
    existing_review = product.reviews.filter(customer=customer).first()

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            stars = form.cleaned_data['stars']
            review_text = form.cleaned_data['review_text']
            if existing_review:
                # Update existing review
                existing_review.stars = stars
                existing_review.review_text = review_text
                existing_review.save()
                messages.success(request, "Your review has been updated.")
            else:
                Review.objects.create(
                    product=product,
                    customer=customer,
                    stars=stars,
                    review_text=review_text
                )
                messages.success(request, "Thank you for your review!")
            return redirect('product_review', product_id=product.id)
    else:
        if existing_review:
            form = ReviewForm(initial={
                'stars': existing_review.stars,
                'review_text': existing_review.review_text
            })
        else:
            form = ReviewForm()
    return render(request, 'store/product_review.html', {
        'product': product,
        'form': form,
        'reviews': reviews,
    })



@login_required
def download_invoice(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user.customerprofile
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)

    width, height = A4
    y = height - 40

    # Store Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, y, "EComStore Invoice")

    y -= 30

    p.setFont("Helvetica", 11)
    p.drawString(40, y, f"Order ID: {order.id}")
    y -= 18

    p.drawString(40, y, f"Order Date: {order.date_of_purchase.strftime('%Y-%m-%d')}")
    y -= 18

    p.drawString(40, y, f"Customer: {order.customer.first_name} {order.customer.last_name}")
    y -= 18

    p.drawString(40, y, f"Payment Status: {order.payment_status}")
    y -= 30

    # Address
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Delivery Address")
    y -= 18

    p.setFont("Helvetica", 11)

    address = order.address
    if address:
        p.drawString(40, y, address.address_line)
        y -= 15
        p.drawString(40, y, f"{address.city}, {address.state}")
        y -= 15
        p.drawString(40, y, f"{address.postal_code}, {address.country}")
        y -= 25

    # Table Header
    p.setFont("Helvetica-Bold", 12)

    p.drawString(40, y, "Product")
    p.drawString(300, y, "Qty")
    p.drawString(350, y, "Price")
    p.drawString(430, y, "Subtotal")

    y -= 10
    p.line(40, y, 520, y)
    y -= 20

    p.setFont("Helvetica", 11)

    total = 0

    for item in order.items.all():

        subtotal = item.quantity * item.price
        total += subtotal

        product_name = item.product.name if item.product else "Deleted product"

        p.drawString(40, y, product_name[:40])
        p.drawString(305, y, str(item.quantity))
        p.drawString(350, y, f"₹{item.price}")
        p.drawString(430, y, f"₹{subtotal}")

        y -= 18

        if y < 80:
            p.showPage()
            y = height - 40

    y -= 10
    p.line(40, y, 520, y)
    y -= 20

    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, "Total")
    p.drawString(430, y, f"₹{total}")

    y -= 40

    p.setFont("Helvetica", 10)
    p.drawString(40, y, "Thank you for shopping with EComStore!")

    p.showPage()
    p.save()

    return response