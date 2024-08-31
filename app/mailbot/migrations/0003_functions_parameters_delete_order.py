# Generated by Django 4.2.3 on 2024-08-30 06:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mailbot', '0002_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Functions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Parameters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('param', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('function', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mailbot.functions')),
            ],
        ),
        migrations.DeleteModel(
            name='Order',
        ),
    ]
