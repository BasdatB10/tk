from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

from .profile_service import get_user_profile_data, update_profile, change_password
from .forms import CustomPasswordChangeForm

@login_required
def profile_view(request):
    username = request.user.username
    
    # Process form submission
    if request.method == 'POST':
        success = update_profile(username, request.POST)
        if success:
            messages.success(request, 'Profil berhasil diperbarui!')
        else:
            messages.error(request, 'Gagal memperbarui profil. Silakan coba lagi.')
        return redirect('base:profile')
    
    # Get user profile data
    profile_data = get_user_profile_data(username)
    if not profile_data:
        messages.error(request, 'Profil tidak ditemukan')
        return redirect('base:home')
    
    return render(request, 'profile.html', profile_data)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            success, message = change_password(
                request.user.username,
                form.cleaned_data['old_password'],
                form.cleaned_data['new_password1'],
                form.cleaned_data['new_password2']
            )
            
            if success:
                # Update session auth hash to keep the user logged in
                update_session_auth_hash(request, request.user)
                messages.success(request, message)
                return redirect('base:profile')
            else:
                messages.error(request, message)
        else:
            messages.error(request, 'Mohon perbaiki kesalahan di bawah ini.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {'form': form})