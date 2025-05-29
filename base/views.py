import psycopg2, os, dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.shortcuts import render, redirect
from functools import wraps
from django.conf import settings

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

@session_required
def dashboard(request):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        username = request.session.get('username')
        
        # Cek role user
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN EXISTS (SELECT 1 FROM PENGUNJUNG WHERE username_P = %s) THEN 'Pengunjung'
                    WHEN EXISTS (SELECT 1 FROM DOKTER_HEWAN WHERE username_DH = %s) THEN 'Dokter Hewan'
                    WHEN EXISTS (SELECT 1 FROM PENJAGA_HEWAN WHERE username_jh = %s) THEN 'Penjaga Hewan'
                    WHEN EXISTS (SELECT 1 FROM PELATIH_HEWAN WHERE username_lh = %s) THEN 'Pelatih Hewan'
                    WHEN EXISTS (SELECT 1 FROM STAF_ADMIN WHERE username_sa = %s) THEN 'Staf Admin'
                END as role
        """, (username, username, username, username, username))
        
        role = cursor.fetchone()[0]
        
        # Ambil data user berdasarkan role
        if role == 'Pengunjung':
            # Data pengunjung
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, pg.alamat, pg.tgl_lahir
                FROM PENGGUNA p
                JOIN PENGUNJUNG pg ON p.username = pg.username_P
                WHERE p.username = %s
            """, (username,))
            user_data = cursor.fetchone()

            # Riwayat kunjungan dari tabel RESERVASI
            cursor.execute("""
                SELECT DISTINCT tanggal_kunjungan
                FROM RESERVASI
                WHERE username_p = %s AND status != 'Dibatalkan'
                ORDER BY tanggal_kunjungan DESC
            """, (username,))
            riwayat_kunjungan = [row[0].strftime('%d %B %Y') for row in cursor.fetchall()]

            # Tiket yang dibeli dari tabel RESERVASI
            cursor.execute("""
                SELECT r.nama_fasilitas, r.jumlah_tiket, r.tanggal_kunjungan,
                       CASE 
                           WHEN a.nama_atraksi IS NOT NULL THEN 'Atraksi'
                           WHEN w.nama_wahana IS NOT NULL THEN 'Wahana'
                       END as jenis_fasilitas
                FROM RESERVASI r
                LEFT JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
                LEFT JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
                WHERE r.username_p = %s AND r.status != 'Dibatalkan'
                ORDER BY r.tanggal_kunjungan DESC
            """, (username,))
            tiket_dibeli = []
            for row in cursor.fetchall():
                tiket_dibeli.append(f"{row[0]} ({row[3]}) - {row[1]}x - Dibeli: {row[2].strftime('%d/%m/%Y')}")

            context = {
                'user_data': [{
                    'username': user_data[0],
                    'email': user_data[1],
                    'nama_depan': user_data[2],
                    'nama_tengah': user_data[3],
                    'nama_belakang': user_data[4],
                    'no_telepon': user_data[5],
                    'role': role,
                    'alamat': user_data[6],
                    'tgl_lahir': user_data[7],
                    'riwayat_kunjungan': riwayat_kunjungan,
                    'tiket_dibeli': tiket_dibeli
                }]
            }
            
        elif role == 'Dokter Hewan':
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, dh.no_STR, s.nama_spesialisasi,
                       (SELECT COUNT(DISTINCT cm.id_hewan)
                        FROM CATATAN_MEDIS cm
                        WHERE cm.username_dh = dh.username_DH) as jumlah_hewan
                FROM PENGGUNA p
                JOIN DOKTER_HEWAN dh ON p.username = dh.username_DH
                LEFT JOIN SPESIALISASI s ON dh.username_DH = s.username_SH
                WHERE p.username = %s
            """, (username,))
            user_data = cursor.fetchone()
            context = {
                'user_data': [{
                    'username': user_data[0],
                    'email': user_data[1],
                    'nama_depan': user_data[2],
                    'nama_tengah': user_data[3],
                    'nama_belakang': user_data[4],
                    'no_telepon': user_data[5],
                    'role': role,
                    'no_STR': user_data[6],
                    'spesialisasi': user_data[7],
                    'jumlah_hewan': user_data[8]
                }]
            }
            
        elif role == 'Penjaga Hewan':
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, jh.id_staf,
                       (SELECT COUNT(DISTINCT m.id_hewan)
                        FROM MEMBERI m
                        WHERE m.username_jh = jh.username_jh) as jumlah_hewan
                FROM PENGGUNA p
                JOIN PENJAGA_HEWAN jh ON p.username = jh.username_jh
                WHERE p.username = %s
            """, (username,))
            user_data = cursor.fetchone()
            context = {
                'user_data': [{
                    'username': user_data[0],
                    'email': user_data[1],
                    'nama_depan': user_data[2],
                    'nama_tengah': user_data[3],
                    'nama_belakang': user_data[4],
                    'no_telepon': user_data[5],
                    'role': role,
                    'id_staf': user_data[6],
                    'jumlah_hewan': user_data[7]
                }]
            }
            
        elif role == 'Pelatih Hewan':
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, lh.id_staf,
                       (SELECT jp.nama_atraksi
                        FROM JADWAL_PENUGASAN jp
                        WHERE jp.username_lh = lh.username_lh
                        AND jp.tgl_penugasan >= NOW()
                        ORDER BY jp.tgl_penugasan ASC
                        LIMIT 1) as jadwal_hari_ini,
                       (SELECT COUNT(DISTINCT bp.id_hewan)
                        FROM JADWAL_PENUGASAN jp
                        JOIN BERPARTISIPASI bp ON jp.nama_atraksi = bp.nama_fasilitas
                        WHERE jp.username_lh = lh.username_lh) as jumlah_hewan,
                       (SELECT 
                           CASE 
                               WHEN jp.tgl_penugasan IS NULL AND f.jadwal > NOW() THEN 'UPCOMING'
                               WHEN jp.tgl_penugasan IS NULL AND f.jadwal <= NOW() THEN 'DUE'
                               WHEN jp.tgl_penugasan IS NOT NULL THEN 'FINISHED'
                           END
                        FROM FASILITAS f
                        LEFT JOIN JADWAL_PENUGASAN jp ON f.nama = jp.nama_atraksi 
                            AND jp.username_lh = lh.username_lh
                        WHERE f.nama IN (
                            SELECT jp2.nama_atraksi 
                            FROM JADWAL_PENUGASAN jp2 
                            WHERE jp2.username_lh = lh.username_lh
                        )
                        ORDER BY f.jadwal DESC
                        LIMIT 1) as status_latihan
                FROM PENGGUNA p
                JOIN PELATIH_HEWAN lh ON p.username = lh.username_lh
                WHERE p.username = %s
            """, (username,))
            user_data = cursor.fetchone()
            context = {
                'user_data': [{
                    'username': user_data[0],
                    'email': user_data[1],
                    'nama_depan': user_data[2],
                    'nama_tengah': user_data[3],
                    'nama_belakang': user_data[4],
                    'no_telepon': user_data[5],
                    'role': role,
                    'id_staf': user_data[6],
                    'jadwal_hari_ini': user_data[7],
                    'jumlah_hewan': user_data[8],
                    'status_latihan': user_data[9]
                }]
            }
            
        elif role == 'Staf Admin':
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, sa.id_staf,
                       (SELECT COALESCE(SUM(r.jumlah_tiket), 0)
                        FROM RESERVASI r
                        WHERE DATE(r.tanggal_kunjungan) = CURRENT_DATE
                        AND r.status != 'Dibatalkan') as ringkasan_penjualan,
                       (SELECT COUNT(DISTINCT r.username_p)
                        FROM RESERVASI r
                        WHERE DATE(r.tanggal_kunjungan) = CURRENT_DATE
                        AND r.status != 'Dibatalkan') as jumlah_pengunjung,
                       (SELECT COALESCE(SUM(ad.total_kontribusi), 0)
                        FROM ADOPTER ad
                        JOIN ADOPSI a ON ad.id_adopter = a.id_adopter
                        WHERE a.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '7 days'
                          AND a.tgl_mulai_adopsi <= CURRENT_DATE) as laporan_mingguan
                FROM PENGGUNA p
                JOIN STAF_ADMIN sa ON p.username = sa.username_sa
                WHERE p.username = %s
            """, (username,))
            user_data = cursor.fetchone()
            context = {
                'user_data': [{
                    'username': user_data[0],
                    'email': user_data[1],
                    'nama_depan': user_data[2],
                    'nama_tengah': user_data[3],
                    'nama_belakang': user_data[4],
                    'no_telepon': user_data[5],
                    'role': role,
                    'id_staf': user_data[6],
                    'ringkasan_penjualan': f'{user_data[7]} tiket',
                    'jumlah_pengunjung': f'{user_data[8]} orang',
                    'laporan_mingguan': f' {user_data[9]}'
                }]
            }
            
        cursor.close()
        conn.close()
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        print('Error:', e)
        return render(request, 'dashboard.html', {'user_data': [], 'error': str(e)})