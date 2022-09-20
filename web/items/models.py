from faulthandler import disable
from statistics import mode
from django.db import models
from django import forms
import stripe
from web import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator

class Item(models.Model):
    name = models.CharField(verbose_name="Имя", max_length=255, unique=True)
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
    def __str__(self):
        return self.name

class Coupon(models.Model):
    id = models.CharField(verbose_name="id", max_length=255, primary_key=True, blank=True)
    name = models.CharField(verbose_name="название", max_length=255, blank=True)
    percent_off = models.FloatField(verbose_name="скидка (в процентах)", validators=[MinValueValidator(0), MaxValueValidator(100)])
    def __str__(self):
        return self.id

@receiver(pre_save, sender=Coupon)
def create_coupon(sender, instance, **kwargs):
    id, name, percent_off = (x if x else None for x in (instance.id, instance.name, instance.percent_off))
    coupon = stripe.Coupon.create(id=id, name=name, percent_off=percent_off)
    if not instance.name:
        instance.name = coupon.name
    if not instance.id:
        instance.id = coupon.id

class PromotionCode(models.Model):
    id = models.CharField(verbose_name="id", max_length=255, primary_key=True, blank=True)
    code = models.CharField(verbose_name="код", max_length=255, blank=True)
    coupon = models.ForeignKey(Coupon, verbose_name="Купон", on_delete=models.CASCADE)
    def __str__(self):
        return self.code

@receiver(pre_save, sender=PromotionCode)
def create_promotion_code(sender, instance, **kwargs):
    id, code, coupon = (x if x else None for x in (instance.id, instance.code, instance.coupon))
    promotion_code = stripe.PromotionCode.create(id=id, code=code, coupon=coupon)
    if not instance.code:
        instance.code = promotion_code.code
    if not instance.id:
        instance.id = promotion_code.id

class Tax(models.Model):
    id = models.CharField(verbose_name="id", max_length=255, primary_key=True, blank=True)
    display_name = models.CharField(verbose_name="название", max_length=255)
    description = models.TextField(verbose_name="описапние", blank=True, null=True)
    inclusive = models.BooleanField()
    percentage = models.FloatField(verbose_name="проценты", validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    def __str__(self):
        return self.display_name

@receiver(pre_save, sender=Tax)
def create_tax(sender, instance, **kwargs):
    id, display_name, description, inclusive, percentage = (x if x else None for x in (instance.id, instance.display_name, instance.description, instance.inclusive, instance.percentage))
    tax = stripe.TaxRate.create(display_name=display_name, description=description, inclusive=inclusive, percentage=percentage)    
    instance.id = tax.id

class OrderManager(models.Manager):
    def current(self, request):
        try:
            return self.get(pk=request.session.get('order'))
        except:
            order = self.create()
            try:
                tax = Tax.objects.get(display_name='НДС')
                order.taxes.add(tax)
            except:
                pass
            request.session['order'] = order.pk
            request.session.modified = True
            return order


class Order(models.Model):
    ORDER_STATUS = (
        ('O', 'Открыт'),
        ('S', 'Подтверждён'),
        ('W', 'Ожидает'),
        ('C', 'Отменён')
    )
    items = models.ManyToManyField(Item, verbose_name = "товары", through="OrderItems")
    status = models.CharField(verbose_name="статус", max_length=1, choices=ORDER_STATUS, default='O')
    promotion_code = models.ForeignKey(PromotionCode, on_delete=models.SET_NULL, verbose_name="промо-код", blank=True, null=True)
    taxes = models.ManyToManyField(Tax, verbose_name="налоги")
    objects = OrderManager()
    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
    def __str__(self):
        return f'заказ №{self.pk}'

class OrderItems(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="заказ")
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, verbose_name="товар")
    count = models.PositiveIntegerField(verbose_name="количество")
    class Meta:
        verbose_name_plural = 'товары в корзине'
        unique_together = ('order', 'item')
    def __str__(self):
        return f"{self.item}: {self.count}"

class OrderItemsForm(forms.ModelForm):
    class Meta:
        model = OrderItems
        fields = ['item', 'order', 'count']
        widgets = {
            'order': forms.HiddenInput(),
            'item': forms.HiddenInput(),
        }
    def __init__(self, *args, **kwargs):
        super(OrderItemsForm, self).__init__(*args, **kwargs)
        self.fields['count'].label = kwargs['instance'].item.name
        print(kwargs)

class OrderItemsCountForm(forms.ModelForm):
    class Meta:
        model = OrderItems
        fields = ['item', 'order', 'count']
        widgets = {
            'order': forms.HiddenInput(),
            'item': forms.HiddenInput(),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'
