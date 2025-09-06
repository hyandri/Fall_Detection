from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from .models import Administrator, Contact
from .forms import AdminInfoForm


def dashboard_view(request):
    # Admin info
    admin = Administrator.objects.first()
    if not admin:
        admin = Administrator.objects.create(email="admin@example.com")

    admin_form = AdminInfoForm(instance=admin)

    # Handle POST for both admin form and new contact
    if request.method == "POST":
        # Check which form is submitted
        if "name" in request.POST:  # this is your Contact form
            name = request.POST.get("name")
            email = request.POST.get("email")
            number = request.POST.get("number")
            whatsapp_enabled = "whatsapp_enabled" in request.POST
            email_enabled = "email_enabled" in request.POST

            Contact.objects.create(
                name=name,
                phone_number=number,
                email=email,
                whatsapp_enabled=whatsapp_enabled,
                email_enabled=email_enabled
            )
            return redirect("dashboard")  # reload page to see new contact

        else:  # assume admin form submitted
            admin_form = AdminInfoForm(request.POST, instance=admin)
            if admin_form.is_valid():
                admin_form.save()
                return redirect("dashboard")

    # Get contacts
    contacts = Contact.objects.all()

    return render(request, "dashboard.html", {
        "form": admin_form,
        "admin": admin,
        "contacts": contacts
    })

def update_admin_info(request):
    if request.method == 'POST':
        admin = Administrator.objects.first()
        form = AdminInfoForm(request.POST, instance=admin)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'email': admin.email, 'phone_number': admin.phone_number})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def delete(request, pk):
    task=get_object_or_404(Contact, pk=pk)
    task.delete()
    return redirect('dashboard')