from django.db import transaction
from .models import Cart, CartItem
from products.models import Product


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@transaction.atomic
def add_to_cart(user, product_id, quantity=1):
    cart = get_or_create_cart(user)

    product = Product.objects.select_for_update().get(id=product_id)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity}
    )

    if not created:
        item.quantity += quantity
        item.save()

    return item


def remove_from_cart(user, product_id):
    cart = get_or_create_cart(user)
    return CartItem.objects.filter(
        cart=cart,
        product_id=product_id
    ).delete()



def update_cart_item(user, product_id, quantity):
    cart = get_or_create_cart(user)

   
    if quantity <= 0:
        remove_from_cart(user, product_id)
        return None  
    
    
    item = CartItem.objects.filter(
        cart=cart, 
        product_id=product_id
    ).first()

    if not item:
        return None

    item.quantity = quantity
    item.save()
    return item