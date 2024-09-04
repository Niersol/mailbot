from .models import *

from django.db.models import Q

def inquiry_about_collection(args):
    name = args['collection_name']
    if name:
        try:
            collection = Collection.objects.get(Q(name__icontains=name))
            products = Product.objects.select_related('images').filter(collection=collection)
            product_list = []
            for product in products:
                if product.stock > 0:
                    product_list.append({
                        'product':product.name,
                        'description':product.description,
                        'price':product.price,
                        'color':product.color,
                        'size':product.size,
                        'weight':product.weight,
                        'brand':product.brand,
                        'Unit':product.sku,
                        'images':product.images
                    })
                    return product_list
                else:
                    return f"The products in {name} collection is currently out of stock."
                    
        except Collection.DoesNotExist:
            return f"The collection of {name} does not exist in our inventory"
    else:
        return f"No collection name was provided"

# def check_product_availability(name, color, size):
#     try:
#         # Using __icontains for partial match and case-insensitive
#         product = Product.objects.get(Q(name__icontains=name), Q(color__icontains=color), Q(size__icontains=size))
        
#         if product.stock > 0:
#             return f"The {name} in {color} color and size {size} is available."
#         else:
#             return f"The {name} in {color} color and size {size} is currently out of stock."
    
#     except Product.DoesNotExist:
#         return f"The {name} in {color} color and size {size} does not exist in our inventory."

# def get_order_status(order_number):
#     try:
#         order = Order.objects.get(order_number=order_number)
#         return f"Your order status is: {order.status}."
#     except Order.DoesNotExist:
#         return "The order number you provided does not exist."

# def process_return(order_number, reason):
#     try:
#         order = Order.objects.get(order_number=order_number)
#         if order.status == 'Delivered':
#             # Logic to process the return
#             return f"Return processed for order {order_number}. Reason: {reason}."
#         else:
#             return "Only delivered orders can be returned."
#     except Order.DoesNotExist:
#         return "The order number you provided does not exist."
