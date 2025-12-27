from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('coordinator', 'Coordinator'),
    ]
    
    PROGRAM_CHOICES = [
        ('STE', 'STE'),
        ('STEM', 'STEM'),
        ('SPFL', 'SPFL'),
        ('SPTVE', 'SPTVE'),
        ('TOP5', 'TOP 5'),
        ('HETERO', 'HETERO'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    program = models.CharField(max_length=20, choices=PROGRAM_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    
    class Meta:
        db_table = 'user_profile'