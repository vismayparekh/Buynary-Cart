from django.db import models
from django.contrib.auth.models import User

# defining database models to save data

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=500)

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through='CartItem')

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  
    def __str__(self):
        return self.user.username