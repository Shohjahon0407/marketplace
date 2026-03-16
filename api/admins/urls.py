from django.urls import path, include

urlpatterns = [
    path('category/', include('api.admins.category.urls')),
    path('product/', include('api.admins.product.urls')),
    path('trash/', include('api.admins.trash.urls')),
    path('order/', include('api.admins.orders.urls')),
]