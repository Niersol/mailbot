from django.db import models
from datetime import timedelta

class APIKey(models.Model):
    api_key = models.CharField(max_length=255)
    
class FineTunningModel(models.Model):
    model_name = models.CharField(max_length=255,null=True,blank=True)
    model_id = models.CharField(max_length=255,unique=True)
    output_model = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField()
    selected = models.BooleanField(default=False)

class FineTuneExample(models.Model):
    user = models.TextField()
    system = models.TextField(null=True,blank=True)
    assistant = models.TextField()

class Functions(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

class Parameters(models.Model):
    function = models.ForeignKey(Functions,on_delete=models.CASCADE)
    param = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

# ##############################
# MOCK MODELS #
# ##############################

from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    style = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=10)
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.style} - {self.color} - {self.size}"

class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    loyalty_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class GiftCard(models.Model):
    card_number = models.CharField(max_length=16, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.card_number
