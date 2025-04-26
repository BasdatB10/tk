from django.shortcuts import render, redirect
from django.contrib.auth import logout

def home(request):
    return render(request, "home.html")

def register(request):
    return render(request, "register.html")

def login(request):
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('base:home')

def dashboard(request):
    pengguna_data = [
        {
            'username': 'anggita.desmawati17',
            'email': 'anggtadesma@gmail.com',
            'password': 'angt09@a!23',
            'nama_depan': 'Anggita',
            'nama_tengah': 'Desmawati',
            'nama_belakang': 'Wahyuni',
            'no_telepon': '087191548622',
            'role': 'Pengunjung',
            'alamat': 'Jl. Merdeka No. 10, Jakarta',
            'tgl_lahir': '1997-03-12',
        },
        {
            'username': 'maximilian.benjamin',
            'email': 'maximilian.benjamin@outlook.com',
            'password': 'maxben@2021!',
            'nama_depan': 'Maximilian',
            'nama_tengah': 'Benjamin',
            'nama_belakang': 'Santosa',
            'no_telepon': '081234398770',
            'role': 'Dokter Hewan',
            'spesialisasi': 'Bedah Hewan',
            'no_STR': 'STR-4928723',
            'jumlah_hewan' : '1',
        },
        {
            'username': 'simone.garcia15',
            'email': 'simone.garcia15@gmail.com',
            'password': 'simone@15Garcia',
            'nama_depan': 'Simone',
            'nama_tengah': 'Garcia',
            'nama_belakang': 'Santos',
            'no_telepon': '085745612323',
            'role': 'Penjaga Hewan',
            'id_staf': 'e8b0c0a7-69bc-4b6e-a5b1-efb5b3e4877b',
            'jumlah_hewan' : '1',
        },
        {
            'username': 'diana.rahmawati12',
            'email': 'diana.rahmawati12@aol.com',
            'password': 'diana@12!Rahma',
            'nama_depan': 'Diana',
            'nama_tengah': 'Rahmawati',
            'nama_belakang': 'Putri',
            'no_telepon': '087653412890',
            'role': 'Pelatih Hewan',
            'id_staf': 'f7a2c1c9-444f-4772-8b6b-8b9ffbda3954',
            'jadwal_hari_ini' : '08:30',
        },
        {
            'username': 'tiffany.margaretha09',
            'email': 'tiffany.margaretha09@yahoo.com',
            'password': 'tiffany09@Marg@tha',
            'nama_depan': 'Tiffany',
            'nama_tengah': 'Margaretha',
            'nama_belakang': 'Sihotang',
            'no_telepon': '085688493823',
            'role': 'Staf Admin',
            'id_staf': 'ed9cf85b-8494-4d75-88cc-17daac5f5086',
        },
    ]
    
    current_role = request.GET.get('role', 'pengunjung')  
    filtered_data = []

    for user in pengguna_data:
        if user['role'].lower() == current_role.lower():
            filtered_data.append(user)

    return render(request, 'dashboard.html', {'user_data': filtered_data})