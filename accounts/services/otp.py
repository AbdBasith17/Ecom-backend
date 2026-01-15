# import random
# from datetime import timedelta
# from django.utils import timezone
# from django.core.mail import send_mail
# from django.conf import settings

# from accounts.models import EmailOTP


# def generate_otp():
    
#     return f"{random.randint(100000, 999999)}"


# def send_email_otp(user):
   
#     otp_code = generate_otp()

#     expires_at = timezone.now() + timedelta(minutes=5)

#     EmailOTP.objects.create(
#         user=user,
#         otp=otp_code,
#         expires_at=expires_at
#     )

#     send_mail(
#         subject="Verify your email",
#         message=f"Your OTP is {otp_code}. It expires in 5 minutes.",
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         recipient_list=[user.email],
#         fail_silently=False,
#     )
