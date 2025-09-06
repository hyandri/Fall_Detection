from django.shortcuts import render, redirect
from django.conf import settings
from twilio.rest import Client

# Twilio setup (keep these in settings.py ideally)
TWILIO_SID = "ACe174d93e3b036d70b94f2a016ef06b2f"
TWILIO_AUTH_TOKEN = "892b9f668d276b80ef6a5b75b66b40ff"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox or business number

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)


def home(request):
    return render(request, "home.html")


def send_alert(request):
    guardians = ["+9779841985769","+9779843385807"]  
    for number in guardians:
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body="⚠️ Fall detected! Please check immediately.",
            to=f"whatsapp:{number}"
        )

    return redirect("home")  