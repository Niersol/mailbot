# Generated by Django 4.2.3 on 2024-08-29 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailbot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('delivery_date', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
