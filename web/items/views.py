from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, Order, OrderItems, PromotionCode, Tax, OrderItemsForm, OrderItemsCountForm
from django.http import HttpResponse, JsonResponse
import stripe
import json
from django.forms import modelformset_factory
from django.urls import reverse
from web import settings

def items(request):
    items = Item.objects.all()
    return render(request, "items/items.html", {'items': items})
def item(request, id):
    item = get_object_or_404(Item, pk=id)
    order = Order.objects.current(request)
    try:
        count = OrderItems.objects.get(order=order, item=item).count
    except OrderItems.DoesNotExist:
        count = 0
    return render(request, 'items/item.html', {'item': item, 'count': count})
def buy(request, id):
    item = Item.objects.get(pk=id)
    session = stripe.checkout.Session.create(
        line_items = [{
            'price_data': {
                'currency': 'RUB',
                'product_data': {
                    'name': item.name,
                    'description': item.description,
                },
                'unit_amount': int(item.price)*100 #сервис воспринимает цену в копейках, не в рублях
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=settings.BASE_URL, 
        cancel_url=settings.BASE_URL 
    )
    return JsonResponse(session)

def order(request):
    print('\n\n\n')
    order = Order.objects.current(request)
    order_items = OrderItems.objects.filter(order=order)
    OrderFormset = modelformset_factory(OrderItems, extra=0, can_delete=True, form=OrderItemsForm)
    if request.method == 'POST':
        formset = OrderFormset(request.POST, queryset=order_items)
        if formset.is_valid():
            print('\n\n\n')
            print('DEL ', [form.cleaned_data for form in formset.deleted_forms ])
            for form in formset:
                if form in formset.deleted_forms:
                    del form
            formset.save()
        else:
            print('FORMSET_ERROR!!!!  ', formset.errors)
    else:
        formset = OrderFormset(queryset=order_items)
    promotion_code = order.promotion_code.code if order.promotion_code else ""
    return render(request, 'items/order.html', {'formset': formset, 'promotion_code': promotion_code})

def order_discount(request):
    order = Order.objects.current(request)
    if request.method == 'POST':
        code = request.POST.get('code', '')
        if code:
            promotion_code = get_object_or_404(PromotionCode, code=code)
            order.promotion_code = promotion_code
        else:
            order.promotion_code = None
        order.save()
        return redirect(reverse('items:order'), code='303')



def order_buy(request):
    order = Order.objects.current(request)
    order_items = OrderItems.objects.filter(order=order)

    session = stripe.checkout.Session.create(
        line_items = [{
            'price_data': {
                'currency': 'RUB',
                'product_data': {
                    'name': items.item.name,
                    'description': items.item.description,
                },
                'unit_amount': int(items.item.price)*100 #сервис воспринимает цену в копейках, не в рублях
            },
            'quantity': items.count,
            'tax_rates': [tax.id for tax in order.taxes.all()],
        } for items in order_items],
        mode='payment',
        discounts = [{
            'promotion_code': order.promotion_code.id,
            }] if order.promotion_code else None,
        success_url = settings.BASE_URL + reverse('items:order_confirm', args=[order.pk,]),
        cancel_url = settings.BASE_URL + reverse('items:order_cancel', args=[order.pk,])
    )
    order.status = 'W'
    order.save() #меняем статус на "ожидаем оплату"
    return redirect(session.url, code=303)

def order_confirm(request, id):
    request.session['order']=None
    order = Order.objects.get(id=id)
    order.status = 'S' #подтверждён
    order.save()
    return render(request, 'items/order_confirm.html')

def order_cancel(request, id):
    request.session['order']=None
    order = Order.objects.get(id=id)
    order.status = 'C' #отклонён
    order.save()
    return render(request, 'items/order_cancel.html')

def add(request):
    if request.method == 'POST':
        order = Order.objects.current(request)
        data = json.loads(request.body)|{'order': order.pk}
        try:
            instanse = OrderItems.objects.get(order=order, item=data['item'])
        except OrderItems.DoesNotExist:
            instanse = None
        items = OrderItemsCountForm(data, instance=instanse)
        if items.is_valid():
            if items.cleaned_data['count'] > 0:
                items.save()
            else:
                instanse.delete()
            return HttpResponse(status=200)
        else:
            print(items.errors)
