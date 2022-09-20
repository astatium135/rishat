from django.urls import path

from . import views

app_name = 'items'
urlpatterns = [
    path('', views.items, name='items'), 
    path('item/<int:id>', views.item, name='item'),
    path('buy/<int:id>', views.buy, name="buy"),
    path('order/add', views.add, name='add'),
    path('order', views.order, name='order'),
    path('order/buy', views.order_buy, name='order_buy'),
    path('order/<int:id>/confirm', views.order_confirm, name='order_confirm'),
    path('order/<int:id>/cancel', views.order_cancel, name='order_cancel'),
    path('order/discount', views.order_discount, name='order_discount')
] 