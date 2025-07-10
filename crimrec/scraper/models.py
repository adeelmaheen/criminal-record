from django.db import models
from django.core.validators import MinLengthValidator

class CriminalRecord(models.Model):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unknown'),
    ]
    
    RACE_CHOICES = [
        ('W', 'White'),
        ('B', 'Black'),
        ('H', 'Hispanic'),
        ('A', 'Asian'),
        ('U', 'Unknown'),
    ]

    defendant_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default='U')
    race = models.CharField(max_length=1, choices=RACE_CHOICES, default='U')
    case_number = models.CharField(max_length=50, unique=True, validators=[MinLengthValidator(5)])
    date_filed = models.DateField()
    charges = models.TextField()
    arrest_citation_date = models.DateField(null=True, blank=True)
    parish = models.CharField(max_length=100)
    alert_available = models.BooleanField(default=False)
    scraped_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_filed']
        indexes = [
            models.Index(fields=['defendant_name']),
            models.Index(fields=['case_number']),
            models.Index(fields=['parish']),
        ]

    def __str__(self):
        return f"{self.defendant_name} - {self.case_number}"


