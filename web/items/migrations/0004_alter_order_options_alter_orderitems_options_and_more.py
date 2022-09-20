# Generated by Django 4.1.1 on 2022-09-19 08:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0003_order_orderitems_order_items'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'заказ', 'verbose_name_plural': 'заказы'},
        ),
        migrations.AlterModelOptions(
            name='orderitems',
            options={'verbose_name_plural': 'товары в корзине'},
        ),
        migrations.AlterUniqueTogether(
            name='orderitems',
            unique_together={('order', 'item')},
        ),
    ]
