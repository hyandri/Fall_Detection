from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Administrator, Contact, ViewerProfile, FallAlert
from .forms import AdminInfoForm

def home(request):
    return render(request, "home.html")

@login_required(login_url='loginout')
def dashboard_view(request):
    # Check if user is setup user (only setup users can access this dashboard)
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'setup':
        messages.warning(request, 'Only setup users can access this dashboard.')
        return redirect('home')
    
    # Admin info
    admin = Administrator.objects.first()
    if not admin:
        admin = Administrator.objects.create(email="admin@example.com")

    admin_form = AdminInfoForm(instance=admin)

    # Handle POST for admin form, contact form, and viewer form
    if request.method == "POST":
        # Check which form is submitted
        if "name" in request.POST and "viewer_email" not in request.POST:  # Contact form
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
            messages.success(request, f'Guardian {name} added successfully.')
            return redirect("dashboard")  # reload page to see new contact

        elif "viewer_email" in request.POST:  # Viewer linking form
            viewer_email = request.POST.get("viewer_email", "").strip()
            viewer_name = request.POST.get("viewer_name", "").strip()
            viewer_phone = request.POST.get("viewer_phone", "").strip()
            
            if not viewer_email:
                messages.error(request, 'Viewer email is required.')
                return redirect("dashboard")
            
            try:
                # Find the viewer user by email
                viewer_user = User.objects.filter(email=viewer_email).first()
                
                if not viewer_user:
                    messages.error(request, f'No user found with email: {viewer_email}. The viewer must sign up first.')
                    return redirect("dashboard")
                
                # Check if user is a viewer type
                if not hasattr(viewer_user, 'userprofile') or viewer_user.userprofile.user_type != 'viewer':
                    messages.error(request, f'User {viewer_email} is not a viewer user. They must sign up as a viewer.')
                    return redirect("dashboard")
                
                # Check if viewer is already linked to this setup user
                existing_viewer = ViewerProfile.objects.filter(
                    setup_user=request.user,
                    user=viewer_user
                ).first()
                
                if existing_viewer:
                    messages.warning(request, f'Viewer {viewer_email} is already linked to your account.')
                    return redirect("dashboard")
                
                # Create ViewerProfile
                ViewerProfile.objects.create(
                    setup_user=request.user,
                    user=viewer_user,
                    name=viewer_name or viewer_user.get_full_name() or viewer_user.username,
                    email=viewer_email,
                    phone_number=viewer_phone,
                    is_active=True
                )
                messages.success(request, f'Viewer {viewer_email} linked successfully!')
                return redirect("dashboard")
                
            except Exception as e:
                messages.error(request, f'Error linking viewer: {str(e)}')
                return redirect("dashboard")

        else:  # assume admin form submitted
            admin_form = AdminInfoForm(request.POST, instance=admin)
            if admin_form.is_valid():
                admin_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect("dashboard")

    # Get contacts
    contacts = Contact.objects.all()
    
    # Get viewers linked to this setup user
    viewers = ViewerProfile.objects.filter(setup_user=request.user).order_by('-created_at')

    # Alert statistics for this setup user (for setup dashboard)
    setup_alerts = FallAlert.objects.filter(setup_user=request.user)
    total_alerts = setup_alerts.count()
    pending_alerts_count = setup_alerts.filter(status='pending').count()
    confirmed_alerts_count = setup_alerts.filter(status='confirmed').count()
    false_alarm_alerts_count = setup_alerts.filter(status='false_alarm').count()

    return render(request, "dashboard.html", {
        "form": admin_form,
        "admin": admin,
        "contacts": contacts,
        "viewers": viewers,
        "total_alerts": total_alerts,
        "pending_alerts_count": pending_alerts_count,
        "confirmed_alerts_count": confirmed_alerts_count,
        "false_alarm_alerts_count": false_alarm_alerts_count,
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
    messages.success(request, 'Guardian deleted successfully.')
    return redirect('dashboard')


@login_required(login_url='loginout')
def delete_viewer(request, pk):
    """Delete a linked viewer"""
    viewer = get_object_or_404(ViewerProfile, pk=pk)
    
    # Ensure only the setup user who owns this viewer can delete it
    if viewer.setup_user != request.user:
        messages.error(request, 'You do not have permission to delete this viewer.')
        return redirect('dashboard')
    
    viewer_email = viewer.email
    viewer.delete()
    messages.success(request, f'Viewer {viewer_email} removed successfully.')
    return redirect('dashboard')


@login_required(login_url='loginout')
def viewer_dashboard_view(request):
    """Viewer dashboard to display and manage fall alerts"""
    # Check if user is viewer type (only viewers can access this dashboard)
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'viewer':
        messages.warning(request, 'Only viewer users can access this dashboard.')
        return redirect('home')
    
    # Get ViewerProfile for current user
    try:
        viewer_profile = ViewerProfile.objects.get(user=request.user)
    except ViewerProfile.DoesNotExist:
        messages.warning(request, 'Your viewer profile is not linked to any setup user. Please contact the setup user to link your account.')
        return redirect('home')
    
    # Get all FallAlert objects for this viewer
    # Alerts where viewer is specifically assigned to this viewer, or alerts for the setup_user without specific viewer assignment
    all_alerts = FallAlert.objects.filter(
        setup_user=viewer_profile.setup_user
    ).filter(
        Q(viewer=viewer_profile) | Q(viewer__isnull=True)
    ).order_by('-timestamp')
    
    # Separate alerts by status
    pending_alerts = all_alerts.filter(status='pending')
    confirmed_alerts = all_alerts.filter(status='confirmed')
    false_alarm_alerts = all_alerts.filter(status='false_alarm')
    
    # Get setup user info
    setup_user = viewer_profile.setup_user
    
    context = {
        'viewer_profile': viewer_profile,
        'setup_user': setup_user,
        'pending_alerts': pending_alerts,
        'confirmed_alerts': confirmed_alerts,
        'false_alarm_alerts': false_alarm_alerts,
        'all_alerts': all_alerts,
        'total_alerts': all_alerts.count(),
        'pending_count': pending_alerts.count(),
        'confirmed_count': confirmed_alerts.count(),
        'false_alarm_count': false_alarm_alerts.count(),
    }
    
    return render(request, "viewer_dashboard.html", context)


@login_required(login_url='loginout')
@require_POST
def confirm_alert(request, alert_id):
    """
    Viewer API: confirm or mark an alert as false alarm.
    Expects POST with 'status' = 'confirmed' or 'false_alarm'.
    Returns JSON.
    """
    # Ensure user is a viewer
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'viewer':
        return JsonResponse(
            {'success': False, 'error': 'Only viewer users can confirm alerts.'},
            status=403,
        )

    # Get ViewerProfile for current user
    try:
        viewer_profile = ViewerProfile.objects.get(user=request.user)
    except ViewerProfile.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Viewer profile not linked to any setup user.'},
            status=400,
        )

    status_value = (request.POST.get('status') or '').strip().lower()
    if status_value not in ('confirmed', 'false_alarm'):
        return JsonResponse(
            {'success': False, 'error': 'Invalid status.'},
            status=400,
        )

    # Alert must belong to this viewer's setup user AND be either:
    # - specifically assigned to this viewer, or
    # - unassigned (viewer is null)
    try:
        alert = (
            FallAlert.objects.filter(setup_user=viewer_profile.setup_user)
            .filter(Q(viewer=viewer_profile) | Q(viewer__isnull=True))
            .get(pk=alert_id)
        )
    except FallAlert.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Alert not found or not assigned to you.'},
            status=404,
        )

    # Update alert
    alert.status = status_value
    alert.confirmed_by = request.user
    alert.confirmed_at = timezone.now()
    alert.save(update_fields=["status", "confirmed_by", "confirmed_at"])

    return JsonResponse(
        {
            'success': True,
            'alert_id': alert.id,
            'status': alert.status,
            'confirmed_at': alert.confirmed_at.isoformat(),
        }
    )