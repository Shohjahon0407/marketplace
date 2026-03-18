from django.urls import path, include

# api.users.urls
urlpatterns = [
    # path('auth/', include('api.users.auth.urls')),
    path('category/', include('api.users.category.urls')),
    path('product/', include('api.users.product.urls')),
    path('cart/', include('api.users.cart.urls')),
    path('auth/', include('api.users.auth.urls')),
    path('order/', include('api.users.orders.urls')),
    path('address/', include('api.users.address.urls')),
    path('wishlist/', include('api.users.wishlist.urls')),
]
