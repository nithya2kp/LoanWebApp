from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class LoanStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class User(AbstractUser,TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_url = models.ImageField(upload_to='profile_images/',blank=True, null=True)
    csv_file_url = models.FileField(upload_to='transaction_csv/',blank=True, null=True)
    pancard = models.CharField(max_length=100,unique=True,null=True)
    aadhar = models.CharField(max_length=100,unique=True,null=True)
    location = models.TextField()
    credit_score = models.FloatField(null=True)

    def __str__(self):
        return self.username
    

class LoanApplication(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,  
        related_name='loan_applications'      
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_amt = models.FloatField()
    interest_rate = models.FloatField()
    disbursement_rate = models.FloatField()
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.PENDING
    )

    def __str__(self):
        return f"Loan application by {self.user.username} on {self.created_at}"
    

class Payment(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,  
        related_name='user_payments'      
    )
    loan_application = models.OneToOneField(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name='loan_payments'
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amt_due = models.FloatField()
    emi_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.PENDING
    )

    def __str__(self):
        return f"Payment for {self.user.username} due on {self.emi_date}"
    

class CreditEvaluation(TimeStampedModel):
    payments = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='credit_evaluation'
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emi_value = models.FloatField()    
    cibil_score = models.FloatField()

    def __str__(self):
        return f"EMI: {self.emi_value}, CIBIL: {self.cibil_score} for Payment {self.payments.id}"
