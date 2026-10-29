from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem, Product
from .auth_views import send_success, send_error
from django.db import transaction

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = CartItem.objects.filter(cart=cart).select_related('product')
        
        valid_items = []
        out_of_stock_items = []
        subtotal = 0
        total_items = 0
        
        for item in items:
            product = item.product
            item_total = float(product.price) * item.quantity
            subtotal += item_total
            total_items += item.quantity
            
            if product.stock_quantity < item.quantity or product.status != 'active':
                out_of_stock_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'requested': item.quantity,
                    'available': product.stock_quantity
                })
                
            valid_items.append({
                'cart_item_id': item.id,
                'product_id': product.id,
                'quantity': item.quantity,
                'name': product.name,
                'brand': product.brand,
                'price': float(product.price),
                'original_price': float(product.original_price) if product.original_price else None,
                'stock_quantity': product.stock_quantity,
                'image_url': product.image_url,
                'sku': product.sku,
                'product_status': product.status,
                'item_total': item_total
            })
            
        shipping_charge = 0.00 if (subtotal >= 999 or subtotal == 0) else 99.00
        tax_amount = float("{:.2f}".format(subtotal * 0.18))
        total_amount = float("{:.2f}".format(subtotal + shipping_charge + tax_amount))
        
        return send_success('Cart retrieved successfully', {
            'cart_id': cart.id,
            'items': valid_items,
            'total_items': total_items,
            'pricing': {
                'subtotal': float("{:.2f}".format(subtotal)),
                'shipping_charge': shipping_charge,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'free_shipping_threshold': 999.00,
                'eligible_for_free_shipping': subtotal >= 999
            },
            'stock_alerts': out_of_stock_items
        })

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        CartItem.objects.filter(cart=cart).delete()
        return send_success('Cart cleared successfully')


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            return send_error('Quantity must be at least 1.', status_code=status.HTTP_400_BAD_REQUEST)
            
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return send_error('Product not found.', status_code=status.HTTP_404_NOT_FOUND)
            
        if product.status != 'active':
            return send_error('This product is currently unavailable.', status_code=status.HTTP_400_BAD_REQUEST)
            
        if product.stock_quantity < quantity:
            return send_error(f'Only {product.stock_quantity} items available in stock.', status_code=status.HTTP_400_BAD_REQUEST)
            
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        new_qty = cart_item.quantity + quantity
        
        if new_qty > product.stock_quantity:
            return send_error(f'Cannot add {quantity} more. You already have {cart_item.quantity} in cart, and total stock is {product.stock_quantity}.', status_code=status.HTTP_400_BAD_REQUEST)
            
        cart_item.quantity = new_qty
        cart_item.save()
        
        return send_success(f'{product.name} added to cart', {'product_id': product.id, 'quantity': quantity})

class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, product_id):
        quantity = int(request.data.get('quantity', 0))
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        if quantity <= 0:
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
            return send_success('Item removed from cart', {'product_id': product_id, 'quantity': 0})
            
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return send_error('Product not found.', status_code=status.HTTP_404_NOT_FOUND)
            
        if quantity > product.stock_quantity:
            return send_error(f'Only {product.stock_quantity} units available in stock.', status_code=status.HTTP_400_BAD_REQUEST)
            
        updated = CartItem.objects.filter(cart=cart, product_id=product_id).update(quantity=quantity)
        if not updated:
            return send_error('Item not found in your cart.', status_code=status.HTTP_404_NOT_FOUND)
            
        return send_success('Cart updated', {'product_id': product.id, 'quantity': quantity})

    @transaction.atomic
    def delete(self, request, product_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return send_success('Item removed from cart', {'product_id': product_id})
