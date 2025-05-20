from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Pengguna, Pengunjung, DokterHewan, Spesialisasi

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    middle_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    
    class Meta:
        model = Pengguna
        fields = ['email', 'first_name', 'middle_name', 'last_name', 'phone']

class PengunjungProfileForm(forms.ModelForm):
    address = forms.CharField(max_length=200, required=True, widget=forms.Textarea)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = Pengunjung
        fields = ['address', 'dob']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'alamat'):
            self.fields['address'].initial = self.instance.alamat
        if self.instance and hasattr(self.instance, 'tgl_lahir'):
            self.fields['dob'].initial = self.instance.tgl_lahir
    
    def save(self, commit=True):
        pengunjung = super().save(commit=False)
        pengunjung.alamat = self.cleaned_data['address']
        pengunjung.tgl_lahir = self.cleaned_data['dob']
        if commit:
            pengunjung.save()
        return pengunjung

class DokterHewanProfileForm(forms.ModelForm):
    SPECIALIZATION_CHOICES = [
        ('mamalia_besar', 'Mamalia Besar'),
        ('reptil', 'Reptil'),
        ('burung_eksotis', 'Burung Eksotis'),
        ('primata', 'Primata'),
        ('lainnya', 'Lainnya'),
    ]
    
    specialization = forms.ChoiceField(choices=SPECIALIZATION_CHOICES, required=True)
    other_specialization = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = DokterHewan
        fields = []  # No direct model fields used, we handle specializations separately
    
    def save(self, user, commit=True):
        dokter = DokterHewan.objects.get(username_DH=user)
        
        # Clear existing specializations
        Spesialisasi.objects.filter(username_SH=dokter).delete()
        
        # Add new specialization
        specialization = self.cleaned_data['specialization']
        if specialization == 'lainnya' and self.cleaned_data.get('other_specialization'):
            Spesialisasi.objects.create(
                username_SH=dokter,
                nama_spesialisasi=self.cleaned_data['other_specialization']
            )
        else:
            Spesialisasi.objects.create(
                username_SH=dokter,
                nama_spesialisasi=dict(self.SPECIALIZATION_CHOICES)[specialization]
            )
        
        return dokter

class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = Pengguna
        fields = []  # No additional fields for staff

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(), label="Password Lama")
    new_password1 = forms.CharField(widget=forms.PasswordInput(), label="Password Baru")
    new_password2 = forms.CharField(widget=forms.PasswordInput(), label="Konfirmasi Password Baru")