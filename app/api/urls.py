from django.contrib import admin
from django.urls import path,include
from .views import ProductListView, ProductDetailView, CollectionListView, CollectionDetailView, CartListView, CartDetailView, OrderListView, OrderDetailView
from .views import ImageListView, ImageDetailView,ChatView

urlpatterns = [
    path('chat/',ChatView.as_view(),name='chat'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/<int:pk>/', CollectionDetailView.as_view(), name='collection-detail'),
    path('carts/', CartListView.as_view(), name='cart-list'),
    path('carts/<int:pk>/', CartDetailView.as_view(), name='cart-detail'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('images/', ImageListView.as_view(), name='image-list'),
    path('images/<int:pk>/', ImageDetailView.as_view(), name='image-detail'),

]

