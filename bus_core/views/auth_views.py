"""
Authentication and Role-Based Access Control Views.
Integrates MongoDB users collection with Django sessions.
"""

from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from ..database.repositories import UserRepository


def auth_context(request):
    """Context processor providing current logged-in user and role to all templates."""
    user = request.session.get('user')
    return {
        'current_user': user,
        'is_authenticated': user is not None,
        'user_role': user.get('role') if user else 'anonymous'
    }


def login_required_mongo(view_func):
    """Decorator ensuring user is authenticated via session."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user'):
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles):
    """Decorator restricting access by role(s)."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.session.get('user')
            if not user:
                messages.warning(request, "Please log in to continue.")
                return redirect('login')
            if user.get('role') not in allowed_roles:
                messages.error(request, f"Access denied. Required role: {', '.join(allowed_roles)}")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def login_view(request):
    """User Login View."""
    if request.session.get('user'):
        role = request.session['user'].get('role')
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'manager':
            return redirect('manager_dashboard')
        elif role == 'driver':
            return redirect('driver_dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user_repo = UserRepository()
        user = user_repo.get_by_username(username)
        if not user:
            # Check by email too
            user = user_repo.get_by_email(username)

        if user and user_repo.verify_password(user, password):
            # Save sanitized user to session
            request.session['user'] = {
                'user_id': user.get('user_id'),
                'username': user.get('username'),
                'email': user.get('email'),
                'role': user.get('role', 'passenger'),
                'full_name': user.get('full_name', username),
                'phone': user.get('phone', '')
            }
            messages.success(request, f"Welcome back, {user.get('full_name', username)}!")

            # Redirect according to role
            role = user.get('role')
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'manager':
                return redirect('manager_dashboard')
            elif role == 'driver':
                return redirect('driver_dashboard')
            return redirect('home')
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'auth/login.html')


def register_view(request):
    """User Registration View."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        role = request.POST.get('role', 'passenger')
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/register.html')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, 'auth/register.html')

        user_repo = UserRepository()
        if user_repo.get_by_username(username):
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'auth/register.html')

        if user_repo.get_by_email(email):
            messages.error(request, f"Email '{email}' is already registered.")
            return render(request, 'auth/register.html')

        # Limit self-registration roles for security
        if role not in ['passenger', 'driver', 'manager']:
            role = 'passenger'

        user = user_repo.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            full_name=full_name,
            phone=phone
        )
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'auth/register.html')


def logout_view(request):
    """User Logout View."""
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('login')
