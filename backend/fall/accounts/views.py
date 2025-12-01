import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


logger = logging.getLogger(__name__)


def _send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verify_url = request.build_absolute_uri(
        reverse('verify_email', args=[uid, token])
    )

    context = {
        'user': user,
        'verification_url': verify_url,
        'site_name': 'FallGuard',
    }

    subject = render_to_string('accounts/email/verify_subject.txt', context).strip()
    text_body = render_to_string('accounts/email/verify_body.txt', context)
    html_body = render_to_string('accounts/email/verify_body.html', context)

    email_message = EmailMultiAlternatives(
        subject=subject or 'Verify your FallGuard account',
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email_message.attach_alternative(html_body, 'text/html')
    email_message.send(fail_silently=False)


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''

        if not username or not email or not password:
            messages.info(request, 'All fields are required.')
            return redirect('signup')

        if len(password) < 8:
            messages.info(request, 'Password must be at least 8 characters long.')
            return redirect('signup')

        has_upper = any(c.isalpha() and c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)

        if not has_upper:
            messages.info(request, 'Password must contain at least one uppercase letter (A-Z).')
            return redirect('signup')

        if not has_symbol:
            messages.info(request, 'Password must contain at least one symbol.')
            return redirect('signup')

        if not has_digit:
            messages.info(request, 'Password must contain at least one number.')
            return redirect('signup')


        if not email.endswith('@gmail.com'):
            messages.info(request, 'Please use a valid Gmail account.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.info(request, 'Username is taken.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.info(request, 'Email is taken.')
            return redirect('signup')

        # Get user_type from POST (default to 'setup' if not provided)
        user_type = request.POST.get('user_type', 'setup')
        if user_type not in ['setup', 'viewer']:
            user_type = 'setup'

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        user.is_active = False
        user.save(update_fields=['is_active'])

        # Update UserProfile with selected user_type
        # Signal handler creates UserProfile with default 'setup', so update if viewer was selected
        if hasattr(user, 'userprofile'):
            user.userprofile.user_type = user_type
            user.userprofile.save(update_fields=['user_type'])

        try:
            _send_verification_email(request, user)
        except Exception as exc:
            logger.exception('Failed to send verification email for %s', user.username)
            user.delete()
            messages.error(
                request,
                'We could not send the verification email. Please try again in a moment.',
            )
            return redirect('signup')

        return render(
            request,
            'accounts/check_email.html',
            {'email': user.email},
        )

    return render(request, 'signup.html')


def loginout(request):
    # If user already logged in, send them to appropriate dashboard
    if request.user.is_authenticated:
        if hasattr(request.user, 'userprofile') and getattr(request.user.userprofile, 'user_type', 'setup') == 'viewer':
            return redirect('viewer_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect based on user type
            if hasattr(user, 'userprofile') and getattr(user.userprofile, 'user_type', 'setup') == 'viewer':
                return redirect('viewer_dashboard')
            return redirect('dashboard')

        pending_user = User.objects.filter(username=username).first()
        if pending_user and not pending_user.is_active:
            messages.info(
                request,
                'Please verify your email before logging in. Check your inbox for the activation link.',
            )
            return redirect('loginout')

        messages.info(request, 'Invalid credentials.')
        return redirect('loginout')

    return render(request, 'loginout.html')


def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect('loginout')


def google_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    google_url = reverse('socialaccount_login', args=['google'])
    return redirect(google_url)


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        messages.success(request, 'Your email has been verified. You can log in now.')
        return redirect('loginout')

    messages.error(
        request,
        'The verification link is invalid or expired. Please sign up again to receive a new link.',
    )
    return redirect('signup')
