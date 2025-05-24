import psycopg2, os, dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.shortcuts import render, redirect
from functools import wraps

dotenv.load_dotenv()

def session_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('base:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def home(request):
    if 'username' in request.session:
        return redirect('base:dashboard')
    return render(request, "home.html")

@csrf_protect
def register(request):
    if 'username' in request.session:
        return redirect('base:dashboard')

    alert_message = None
    if request.method == "POST":
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()

            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            nama_depan = request.POST.get("nama_depan")
            nama_tengah = request.POST.get("nama_tengah", "")
            nama_belakang = request.POST.get("nama_belakang")
            no_telepon = request.POST.get("no_telepon")
            role = request.POST.get("role")
            cursor.execute("""
                INSERT INTO SIZOPI.PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon))

            if role == "pengunjung":
                alamat = request.POST.get("alamat")
                tgl_lahir = request.POST.get("tgl_lahir")
                cursor.execute("""
                    INSERT INTO SIZOPI.PENGUNJUNG (username_P, alamat, tgl_lahir)
                    VALUES (%s, %s, %s);
                """, (username, alamat, tgl_lahir))

            elif role == "dokter_hewan":
                no_STR = request.POST.get("no_STR")
                nama_spesialisasi = request.POST.get("nama_spesialisasi")
                cursor.execute("""
                    INSERT INTO DOKTER_HEWAN (username_DH, no_STR)
                    VALUES (%s, %s);
                """, (username, no_STR))
                cursor.execute("""
                    INSERT INTO SPESIALISASI (username_SH, nama_spesialisasi)
                    VALUES (%s, %s);
                """, (username, nama_spesialisasi))

            elif role == "staf":
                id_staf = request.POST.get("id_staf")
                role_staf = request.POST.get("role_staf")
                if role_staf == "penjaga_hewan":
                    cursor.execute("""
                        INSERT INTO PENJAGA_HEWAN (username_jh, id_staf)
                        VALUES (%s, %s);
                    """, (username, id_staf))
                elif role_staf == "pelatih_hewan":
                    cursor.execute("""
                        INSERT INTO PELATIH_HEWAN (username_lh, id_staf)
                        VALUES (%s, %s);
                    """, (username, id_staf))
                elif role_staf == "staf_admin":
                    cursor.execute("""
                        INSERT INTO STAF_ADMIN (username_sa, id_staf)
                        VALUES (%s, %s);
                    """, (username, id_staf))

            conn.commit()
            return JsonResponse({'success': True, 'message': 'Pengguna baru berhasil dibuat.'})
        except psycopg2.Error as e:
            alert_message = str(e).split("\n")[0].replace("ERROR:", "").strip()
            return JsonResponse({'success': False, 'message': alert_message}, status=400)
        except Exception:
            alert_message = "Terjadi kesalahan saat melakukan registrasi."
            return JsonResponse({'success': False, 'message': alert_message}, status=400)
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
    return render(request, 'register.html')

@csrf_protect
def login(request):
    if 'username' in request.session:
        return redirect('base:dashboard')

    alert_message = None
    if request.method == "POST":
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()

            email = request.POST.get("email")
            password = request.POST.get("password")
            cursor.execute("""
                INSERT INTO SIZOPI.PERCOBAAN_LOGIN (email, password)
                VALUES (%s, %s);
            """, (email, password))

            cursor.execute("""
                SELECT username FROM SIZOPI.PENGGUNA WHERE email = %s;
            """, (email,))
            result = cursor.fetchone()
            conn.commit()
            
            username = result[0]
            request.session['username'] = username
            request.session['email'] = email
            alert_message = f'Login berhasil. Selamat datang, {username}.'
            return JsonResponse({'success': True, 'message': alert_message, 'username': username, 'email': email})
        except psycopg2.Error as e:
            alert_message = str(e).split("\n")[0].replace("ERROR:", "").strip()
            return JsonResponse({'success': False, 'message': alert_message}, status=401)
        except Exception:
            alert_message = "Terjadi kesalahan saat proses login."
            return JsonResponse({'success': False, 'message': alert_message}, status=400)
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
    return render(request, 'login.html')

@csrf_exempt
def logout(request):
    request.session.flush()
    return redirect('base:home')

def profile(request):
    return render(request, "profile.html")

def profile_dokter(request):
    return render(request, "profile_dokter.html")

def profile_pengunjung(request):
    return render(request, "profile_pengunjung.html")

def profile_staff(request):
    return render(request, "profile_staff.html")

@session_required
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