# Generated by Django 4.2.1 on 2023-05-09 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0002_category_listing_comment_bid'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='current_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]