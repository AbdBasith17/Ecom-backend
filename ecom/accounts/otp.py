from django.core.mail import send_mail

def send_otp_email(email, otp):
    send_mail(
        subject="OTP Verification",
        message=f"Your OTP is {otp}",
        from_email="basipp123@example.com",
        recipient_list=[email],
        fail_silently=False
    )