from django.core.mail import send_mail

def send_otp_email(email, otp):
    send_mail(
        subject="OTP Verification for Perfaura",
        message=f"Your OTP is {otp}",
        from_email="basipp123@gmail.com",
        recipient_list=[email],
        fail_silently=False
    )