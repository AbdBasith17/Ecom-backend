from django.template.loader import render_to_string
from django.core.mail import EmailMessage

def send_otp_email(email, otp):
    context = {'otp': otp}
    html_content = render_to_string('emails/otp_email.html', context)
    
    email_message = EmailMessage(
        subject="Verify your Perfaura Account",
        body=html_content,
        from_email="basipp123@gmail.com",
        to=[email],
    )
    email_message.content_subtype = "html" 