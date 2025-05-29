from django.shortcuts import render, redirect
import psycopg2
from django.conf import settings
import uuid
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.http import JsonResponse
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required

# Fungsi untuk memeriksa apakah user adalah admin
def is_staf_admin(user):
    # Jika user tidak terautentikasi, langsung kembalikan False
    if not user.is_authenticated:
        return False

    username = user.username

    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        # Periksa apakah username ada di tabel SIZOPI.staf_admin
        cur.execute("SELECT 1 FROM SIZOPI.staf_admin WHERE username_sa = %s", (username,))
        result = cur.fetchone()
        return result is not None # Mengembalikan True jika ditemukan, False jika tidak
    except Exception as e:
        # Log error jika terjadi masalah koneksi/query database, lalu kembalikan False
        print(f"Error checking admin status for user {username}: {e}")
        return False
    finally:
        # Pastikan koneksi database ditutup
        if cur:
            cur.close()
        if conn:
            conn.close()

# Terapkan decorator pada view yang hanya bisa diakses admin
# @login_required # Pastikan user sudah login dulu
# @user_passes_test(is_staf_admin, login_url='home') # Cek apakah user admin, redirect ke 'login' jika bukan
def manage_adopt(request):
    # Koneksi ke database
    conn = psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT']
    )
    
    cur = conn.cursor()
    
    # Ambil data hewan dengan left join seperti biasa
    cur.execute("""
        WITH latest_adopsi AS (
            SELECT 
                id_hewan,
                MAX(tgl_berhenti_adopsi) as latest_end_date
            FROM SIZOPI.adopsi
            GROUP BY id_hewan
        ),
        earliest_adopsi AS (
            SELECT 
                id_hewan,
                MIN(tgl_mulai_adopsi) as earliest_start_date
            FROM SIZOPI.adopsi
            GROUP BY id_hewan
        )
        SELECT 
            h.id, h.nama, h.spesies, h.asal_hewan, h.tanggal_lahir, h.status_kesehatan, h.nama_habitat, h.url_foto,
            a.id_adopter, ea.earliest_start_date as tgl_mulai_adopsi, la.latest_end_date as tgl_berhenti_adopsi, 
            a.status_pembayaran, a.kontribusi_finansial,
            ad.username_adopter
        FROM SIZOPI.hewan h
        LEFT JOIN SIZOPI.adopsi a ON h.id = a.id_hewan
        LEFT JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
        LEFT JOIN latest_adopsi la ON h.id = la.id_hewan
        LEFT JOIN earliest_adopsi ea ON h.id = ea.id_hewan
        WHERE a.tgl_berhenti_adopsi = la.latest_end_date OR a.tgl_berhenti_adopsi IS NULL
    """)
    
    columns = [desc[0] for desc in cur.description]
    hewan_list = []
    for row in cur.fetchall():
        hewan_dict = dict(zip(columns, row))
        hewan_dict['sudah_diadopsi'] = hewan_dict['id_adopter'] is not None
        hewan_list.append(hewan_dict)

    cur.close()
    conn.close()
    
    # Baca parameter GET untuk prefill popup (jika ada)
    prefill_username = request.GET.get('username', '')
    prefill_tipe = request.GET.get('tipe', '')
    prefill_id_hewan = request.GET.get('id_hewan', '')

    show_adopter_form = request.GET.get('show_adopter_form', 'False') == 'True'
    show_user_registration = request.GET.get('show_user_registration', 'False') == 'True'

    pengguna_data = None
    adopter_specific_data = None
    if prefill_username:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        cur.execute("SELECT username, email, nama_depan, nama_belakang, no_telepon FROM SIZOPI.pengguna WHERE username = %s", (prefill_username,))
        pengguna = cur.fetchone()
        if pengguna:
            # Konversi tuple hasil query menjadi dictionary
            pengguna_columns = ['username', 'email', 'nama_depan', 'nama_belakang', 'no_telepon']
            pengguna_data = dict(zip(pengguna_columns, pengguna))
        cur.close()
        conn.close()

        # Jika sedang menampilkan form adopsi dan ada prefill_username, cek data adopter spesifik
        if show_adopter_form and prefill_tipe:
            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cur = conn.cursor()

            # Cari id_adopter berdasarkan username_adopter
            cur.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", (prefill_username,))
            adopter_result = cur.fetchone()

            if adopter_result:
                id_adopter = adopter_result[0]

                if prefill_tipe == 'individu':
                    # Ambil data dari tabel individu
                    cur.execute("SELECT nik, nama FROM SIZOPI.individu WHERE id_adopter = %s", (id_adopter,))
                    individu_data = cur.fetchone()
                    if individu_data:
                        individu_columns = ['nik', 'nama']
                        adopter_specific_data = dict(zip(individu_columns, individu_data))
                        # Gabungkan dengan data pengunjung (alamat, tgl_lahir)
                        cur.execute("SELECT alamat, tgl_lahir FROM SIZOPI.pengunjung WHERE username_p = %s", (prefill_username,))
                        pengunjung_data_adopter = cur.fetchone()
                        if pengunjung_data_adopter:
                            adopter_specific_data['alamat'] = pengunjung_data_adopter[0]
                            adopter_specific_data['tgl_lahir'] = pengunjung_data_adopter[1]

                elif prefill_tipe == 'organisasi':
                    # Ambil data dari tabel organisasi
                    cur.execute("SELECT npp, nama_organisasi FROM SIZOPI.organisasi WHERE id_adopter = %s", (id_adopter,))
                    organisasi_data = cur.fetchone()
                    if organisasi_data:
                        organisasi_columns = ['npp', 'nama_organisasi']
                        adopter_specific_data = dict(zip(organisasi_columns, organisasi_data))
                        # Gabungkan dengan data pengunjung (alamat)
                        cur.execute("SELECT alamat FROM SIZOPI.pengunjung WHERE username_p = %s", (prefill_username,))
                        pengunjung_data_adopter = cur.fetchone()
                        if pengunjung_data_adopter:
                            adopter_specific_data['alamat'] = pengunjung_data_adopter[0]

            cur.close()
            conn.close()

    return render(request, "manage_adopt.html", {
        "hewan_list": hewan_list,
        "show_adopter_form": show_adopter_form,
        "show_user_registration": show_user_registration,
        "prefill_username": prefill_username,
        "prefill_tipe": prefill_tipe,
        "prefill_id_hewan": prefill_id_hewan,
        "pengguna_data": pengguna_data,
        "adopter_specific_data": adopter_specific_data
    })


def show_adopter_page(request):
    # Pastikan user sudah login dengan mengecek session
    if 'username' not in request.session:
        print("Debug - User not logged in, redirecting to login")
        return redirect('base:login')

    username = request.session['username']
    print(f"Debug - Username from session: {username}")
    
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()

        # Cari id_adopter berdasarkan username
        cur.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", (username,))
        adopter_result = cur.fetchone()
        print(f"Debug - Adopter result: {adopter_result}")

        if not adopter_result:
            # Jika user belum menjadi adopter, tampilkan pesan
            print("Debug - User is not an adopter")
            return render(request, "adopter_page.html", {
                "error": "Anda belum mengadopsi satwa apapun. Silakan kunjungi halaman adopsi untuk memulai.",
                "hewan_list": []
            })

        id_adopter = adopter_result[0]
        print(f"Debug - Found adopter_id: {id_adopter}")

        # Ambil nama adopter (individu atau organisasi)
        cur.execute("""
            SELECT COALESCE(i.nama, o.nama_organisasi)
            FROM SIZOPI.adopter a
            LEFT JOIN SIZOPI.individu i ON a.id_adopter = i.id_adopter
            LEFT JOIN SIZOPI.organisasi o ON a.id_adopter = o.id_adopter
            WHERE a.username_adopter = %s
        """, (username,))
        adopter_name_result = cur.fetchone()
        adopter_name = adopter_name_result[0] if adopter_name_result else "Nama Adopter Tidak Ditemukan"
        print(f"Debug - Found adopter name: {adopter_name}")

        # Ambil detail adopter (tipe, NIK/NPP, alamat, telepon)
        adopter_details = {'tipe': None, 'nik': None, 'npp': None, 'alamat': None, 'no_telepon': None}
        
        # Cek tipe adopter dan ambil detail spesifik
        cur.execute("SELECT nik, nama FROM SIZOPI.individu WHERE id_adopter = %s", (id_adopter,))
        individu_data = cur.fetchone()
        if individu_data:
            adopter_details['tipe'] = 'individu'
            adopter_details['nik'] = individu_data[0]
            # Nama sudah diambil sebelumnya

        if not adopter_details['tipe']:
             cur.execute("SELECT npp, nama_organisasi FROM SIZOPI.organisasi WHERE id_adopter = %s", (id_adopter,))
             organisasi_data = cur.fetchone()
             if organisasi_data:
                 adopter_details['tipe'] = 'organisasi'
                 adopter_details['npp'] = organisasi_data[0]
                 # Nama sudah diambil sebelumnya

        # Ambil alamat dan no_telepon dari tabel pengguna/pengunjung berdasarkan username
        cur.execute("SELECT p.alamat, pg.no_telepon FROM SIZOPI.pengunjung p JOIN SIZOPI.pengguna pg ON p.username_p = pg.username WHERE p.username_p = %s", (username,))
        pengunjung_pengguna_data = cur.fetchone()
        if pengunjung_pengguna_data:
            adopter_details['alamat'] = pengunjung_pengguna_data[0]
            adopter_details['no_telepon'] = pengunjung_pengguna_data[1]

        # Konversi UUID ke string sebelum menambahkannya ke dictionary
        adopter_details['id_adopter'] = str(id_adopter)

        print(f"Debug - Found adopter details: {adopter_details}")

        # Konversi adopter_details ke JSON string untuk dilewatkan ke template
        adopter_details_json = json.dumps(adopter_details)
        print(f"Debug - Adopter details as JSON string: {adopter_details_json}")

        # Ambil data hewan yang diadopsi oleh adopter ini
        cur.execute("""
            WITH latest_adopsi AS (
                SELECT 
                    id_hewan,
                    MAX(tgl_berhenti_adopsi) as latest_end_date
                FROM SIZOPI.adopsi
                WHERE id_adopter = %s
                GROUP BY id_hewan
            ),
            earliest_adopsi AS (
                SELECT 
                    id_hewan,
                    MIN(tgl_mulai_adopsi) as earliest_start_date
                FROM SIZOPI.adopsi
                WHERE id_adopter = %s
                GROUP BY id_hewan
            ),
            total_kontribusi AS (
                SELECT 
                    id_hewan,
                    SUM(kontribusi_finansial) as total_kontribusi
                FROM SIZOPI.adopsi
                WHERE id_adopter = %s
                GROUP BY id_hewan
            )
            SELECT 
                h.id,
                h.nama,
                h.spesies,
                h.asal_hewan,
                h.tanggal_lahir,
                h.status_kesehatan,
                h.nama_habitat,
                h.url_foto,
                ea.earliest_start_date as tgl_mulai_adopsi,
                la.latest_end_date as tgl_berhenti_adopsi,
                a.status_pembayaran,
                tc.total_kontribusi as kontribusi_finansial
            FROM SIZOPI.hewan h
            JOIN SIZOPI.adopsi a ON h.id = a.id_hewan
            JOIN latest_adopsi la ON h.id = la.id_hewan
            JOIN earliest_adopsi ea ON h.id = ea.id_hewan
            JOIN total_kontribusi tc ON h.id = tc.id_hewan
            WHERE a.id_adopter = %s
            AND a.tgl_berhenti_adopsi = la.latest_end_date
            ORDER BY ea.earliest_start_date DESC
        """, (id_adopter, id_adopter, id_adopter, id_adopter))

        columns = [desc[0] for desc in cur.description]
        hewan_list = []
        for row in cur.fetchall():
            hewan_dict = dict(zip(columns, row))
            # Hitung usia hewan
            if hewan_dict['tanggal_lahir']:
                today = datetime.date.today()
                age = today.year - hewan_dict['tanggal_lahir'].year
                if today.month < hewan_dict['tanggal_lahir'].month or (today.month == hewan_dict['tanggal_lahir'].month and today.day < hewan_dict['tanggal_lahir'].day):
                    age -= 1
                hewan_dict['usia'] = age
            else:
                hewan_dict['usia'] = None
            hewan_list.append(hewan_dict)

        print(f"Debug - Found {len(hewan_list)} adopted animals")

        # Ambil data rekam medis untuk setiap hewan
        for hewan in hewan_list:
            cur.execute("""
                SELECT
                    cm.tanggal_pemeriksaan,
                    pg.nama_depan || COALESCE(' ' || pg.nama_tengah, '') || ' ' || pg.nama_belakang as nama_dokter,
                    cm.status_kesehatan,
                    cm.diagnosis,
                    cm.pengobatan,
                    cm.catatan_tindak_lanjut
                FROM SIZOPI.catatan_medis cm
                JOIN SIZOPI.dokter_hewan dh ON cm.username_dh = dh.username_dh
                JOIN SIZOPI.pengguna pg ON dh.username_dh = pg.username
                WHERE cm.id_hewan = %s
                ORDER BY cm.tanggal_pemeriksaan DESC
            """, (hewan['id'],))

            rekam_medis_columns = [desc[0] for desc in cur.description]
            rekam_medis_list_raw = cur.fetchall()
            
            # Format data rekam medis agar sesuai dengan JSON (tanggal jadi string)
            rekam_medis_list_formatted = []
            for rm_row in rekam_medis_list_raw:
                rm_dict = dict(zip(rekam_medis_columns, rm_row))
                # Konversi tanggal ke string YYYY-MM-DD
                if isinstance(rm_dict['tanggal_pemeriksaan'], datetime.date):
                    rm_dict['tanggal_pemeriksaan'] = rm_dict['tanggal_pemeriksaan'].isoformat()
                rekam_medis_list_formatted.append(rm_dict)

            # Gunakan json.dumps untuk mengubah list dictionary Python menjadi string JSON valid
            hewan['rekam_medis'] = json.dumps(rekam_medis_list_formatted)

        return render(request, "adopter_page.html", {
            "hewan_list": hewan_list,
            "adopter_name": adopter_name,
            "adopter_details_json": adopter_details_json # Gunakan nama baru untuk JSON string
        })

    except Exception as e:
        print(f"Error in show_adopter_page: {e}")
        return render(request, "adopter_page.html", {
            "error": "Terjadi kesalahan saat mengambil data hewan.",
            "hewan_list": []
        })
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# @login_required # Pastikan user sudah login dulu
# @user_passes_test(is_staf_admin, login_url='login') # Cek apakah user admin, redirect ke 'login' jika bukan
def show_adopter_list(request):
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()

        # Query utama daftar adopter
        cur.execute("""
            SELECT
                a.id_adopter,
                a.username_adopter,
                a.total_kontribusi,
                COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                peng.alamat,
                p.no_telepon
            FROM SIZOPI.adopter a
            LEFT JOIN SIZOPI.individu i ON a.id_adopter = i.id_adopter
            LEFT JOIN SIZOPI.organisasi o ON a.id_adopter = o.id_adopter
            LEFT JOIN SIZOPI.pengguna p ON a.username_adopter = p.username
            LEFT JOIN SIZOPI.pengunjung peng ON a.username_adopter = peng.username_p
            ORDER BY a.total_kontribusi DESC
        """)

        columns = [desc[0] for desc in cur.description]
        adopter_list = []
        adopter_rows = cur.fetchall()

        for row in adopter_rows:
            adopter_dict = dict(zip(columns, row))

            # Ambil data adopsi dengan agregasi dan filter (hanya yang semua periodenya Lunas)
            # Query ini hanya perlu mendapatkan data adopsi, tidak memfilter adopter utama
            cur.execute("""
                WITH aggregated_adopsi AS (
                    SELECT
                        id_hewan,
                        MIN(tgl_mulai_adopsi) as earliest_start_date,
                        MAX(tgl_berhenti_adopsi) as latest_end_date,
                        SUM(kontribusi_finansial) as total_kontribusi_hewan,
                        COUNT(*) as total_periods,
                        COUNT(*) FILTER (WHERE status_pembayaran = 'Lunas') as lunas_periods
                    FROM SIZOPI.adopsi
                    WHERE id_adopter = %s
                    GROUP BY id_hewan
                )
                SELECT
                    h.id as id_hewan,
                    h.nama as nama_hewan,
                    h.spesies as jenis,
                    aa.earliest_start_date as tanggal_mulai,
                    aa.latest_end_date as tanggal_akhir,
                    aa.total_kontribusi_hewan as nominal,
                    (aa.total_periods = aa.lunas_periods) as all_lunas
                FROM SIZOPI.hewan h
                JOIN aggregated_adopsi aa ON h.id = aa.id_hewan
                -- Tetap filter di sini agar hanya mendapatkan adopsi yang semua periodenya Lunas
                WHERE (aa.total_periods = aa.lunas_periods)
                ORDER BY aa.earliest_start_date DESC
            """, (adopter_dict['id_adopter'],))

            adoption_columns = [desc[0] for desc in cur.description]
            adoptions = []
            for adoption_row in cur.fetchall():
                adoption_dict = dict(zip(adoption_columns, adoption_row))
                adoption_dict['status'] = 'Lunas' # Status dummy, karena kita hanya mengambil yang Lunas
                adoptions.append(adoption_dict)

            adopter_dict['adoptions'] = adoptions # Adopsi list per adopter
            adopter_list.append(adopter_dict)

        # --- Query Top 5 Adopter ---
        cur.execute("""
            SELECT
                rank_order,
                id_adopter,
                username_adopter,
                nama_adopter,
                total_kontribusi_periode
            FROM SIZOPI.top_adopters_ranking
            ORDER BY rank_order ASC
            LIMIT 5
        """)
        top_adopters_columns = [desc[0] for desc in cur.description]
        top_5_adopters = []
        for row in cur.fetchall():
            top_adopters_dict = dict(zip(top_adopters_columns, row))
            top_5_adopters.append(top_adopters_dict)

        # Paginasi (jika diperlukan)
        page = request.GET.get('page', 1)
        paginator = Paginator(adopter_list, 10) # 10 adopter per halaman

        try:
            adopter_list_page = paginator.page(page)
        except PageNotAnInteger:
            adopter_list_page = paginator.page(1)
        except EmptyPage:
            adopter_list_page = paginator.page(paginator.num_pages)

        return render(request, "adopter_list.html", {
            "adopter_list": adopter_list_page, # Gunakan objek Paginator.page
            "top_5_adopters": top_5_adopters
        })

    except Exception as e:
        print(f"Error in show_adopter_list: {e}")
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def daftar_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        nama_depan = request.POST.get("nama_depan")
        nama_tengah = request.POST.get("nama_tengah")  # Ambil nama tengah, bisa None
        nama_belakang = request.POST.get("nama_belakang")
        no_telepon = request.POST.get("no_telepon")
        alamat = request.POST.get("alamat")
        tgl_lahir = request.POST.get("tgl_lahir")
        
        # Ambil data dari form (sebelumnya dari session/query string)
        tipe = request.POST.get("tipe")
        id_hewan = request.POST.get("id_hewan")

        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()

        try:
            # Insert ke pengguna dengan nama_tengah
            cur.execute(
                "INSERT INTO SIZOPI.pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
            )
            
            # Insert ke pengunjung
            cur.execute(
                "INSERT INTO SIZOPI.pengunjung (username_p, alamat, tgl_lahir) VALUES (%s, %s, %s)",
                (username, alamat, tgl_lahir)
            )
            
            conn.commit()
            
            # Redirect kembali ke manage_adopt dengan parameter untuk menampilkan form adopsi lengkap
            # Sertakan juga data username, tipe, dan id_hewan
            return redirect(f'/adoption/?show_adopter_form=True&username={username}&tipe={tipe}&id_hewan={id_hewan}')
            
        except Exception as e:
            conn.rollback()
            # Jika gagal, kembali ke manage_adopt dan tampilkan popup registrasi dengan error
            return render(request, "manage_adopt.html", {
                "error": "Gagal mendaftarkan user: " + str(e),
                "show_user_registration": True,
                "prefill_username": username,
                "prefill_tipe": tipe,
                "prefill_id_hewan": id_hewan
            })
        finally:
            cur.close()
            conn.close()

    # Jika GET request ke /daftar-user/ tanpa POST data (tidak seharusnya terjadi dalam alur ini)
    return redirect('adoption_management:manage_adopt')


@csrf_exempt
def daftar_adopter(request):
    if request.method == "POST":
        tipe = request.POST.get("tipe")
        id_hewan = request.POST.get("id_hewan")
        kontribusi = int(request.POST.get("kontribusi"))
        periode = int(request.POST.get("periode"))
        tgl_mulai = datetime.date.today()
        # Hitung tanggal berhenti, pastikan timedelta menggunakan days yang benar
        # 3 bulan -> 90 hari, 6 bulan -> 180 hari, 12 bulan -> 365 hari (kira-kira)
        days_periode = {3: 90, 6: 180, 12: 365}.get(periode, periode*30) # Fallback ke *30 jika nilai tidak standar
        tgl_berhenti = tgl_mulai + datetime.timedelta(days=days_periode)
        status_pembayaran = "tertunda"
        username_adopter = request.POST.get("username") # Ambil username dari hidden field

        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()

        try:
            id_adopter = None
            # Cek apakah username_adopter sudah ada di tabel adopter
            cur.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", (username_adopter,))
            adopter_result = cur.fetchone()

            if adopter_result:
                id_adopter = adopter_result[0]
            else:
                # Jika belum ada, buat id_adopter baru dan tambahkan ke adopter
                id_adopter = str(uuid.uuid4())
                cur.execute(
                   "INSERT INTO SIZOPI.adopter (id_adopter, username_adopter, total_kontribusi) VALUES (%s, %s, %s)",
                   (id_adopter, username_adopter, 0) # Inisialisasi total_kontribusi dengan 0
                )

            # 1. Cek/tambah ke individu & organisasi (jika belum ada)
            if tipe == "individu":
                nik = request.POST.get("nik") # Ambil NIK dari form
                nama = request.POST.get("nama") # Ambil nama dari form (sudah prefill dari pengguna_data)

                # Cek di individu berdasarkan NIK
                cur.execute("SELECT id_adopter FROM SIZOPI.individu WHERE nik = %s", (nik,))
                individu_result = cur.fetchone()
                if not individu_result:
                     # Jika belum ada di individu, tambahkan data individu baru dengan id_adopter yang sudah didapat
                     cur.execute(
                         "INSERT INTO SIZOPI.individu (nik, nama, id_adopter) VALUES (%s, %s, %s)",
                         (nik, nama, id_adopter)
                     )

            elif tipe == "organisasi":
                nama_organisasi = request.POST.get("nama_organisasi")
                npp = request.POST.get("npp")

                # Cek di organisasi berdasarkan NPP
                cur.execute("SELECT id_adopter FROM SIZOPI.organisasi WHERE npp = %s", (npp,))
                organisasi_result = cur.fetchone()
                if not organisasi_result:
                     # Jika belum ada di organisasi, tambahkan data organisasi baru dengan id_adopter yang sudah didapat
                     cur.execute(
                         "INSERT INTO SIZOPI.organisasi (npp, nama_organisasi, id_adopter) VALUES (%s, %s, %s)",
                         (npp, nama_organisasi, id_adopter)
                     )
            else:
                raise ValueError("Tipe adopter tidak valid.")

            # 2. Insert ke tabel adopsi
            # Pastikan id_adopter valid sebelum insert ke adopsi
            if id_adopter:
                cur.execute(
                    """
                    INSERT INTO SIZOPI.adopsi (id_adopter, id_hewan, tgl_mulai_adopsi, tgl_berhenti_adopsi, status_pembayaran, kontribusi_finansial)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (id_adopter, id_hewan, tgl_mulai, tgl_berhenti, status_pembayaran, kontribusi)
                )
            else:
                 raise Exception("ID Adopter tidak ditemukan atau gagal dibuat.")

            conn.commit()
            return redirect('adoption_management:manage_adopt')

        except Exception as e:
            conn.rollback()
            # Jika gagal, kembali ke manage_adopt dan tampilkan form adopsi lengkap dengan error
            # Sertakan juga data username, tipe, dan id_hewan agar form bisa muncul lagi
            return render(request, "manage_adopt.html", {
                 "error": "Gagal mendaftarkan adopsi: " + str(e),
                 "show_adopter_form": True,
                 "prefill_username": username_adopter,
                 "prefill_tipe": tipe,
                 "prefill_id_hewan": id_hewan,
                 "pengguna_data": get_pengguna_data(username_adopter) # Ambil ulang data pengguna
            })

        finally:
            cur.close()
            conn.close()

    return redirect('adoption_management:manage_adopt')

# Fungsi pembantu untuk ambil data hewan
def get_hewan_list():
    conn = psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT']
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            h.id, h.nama, h.spesies, h.asal_hewan, h.tanggal_lahir, h.status_kesehatan, h.nama_habitat, h.url_foto,
            a.id_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.status_pembayaran, a.kontribusi_finansial,
            ad.username_adopter
        FROM SIZOPI.hewan h
        LEFT JOIN SIZOPI.adopsi a ON h.id = a.id_hewan
        LEFT JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
    """)
    columns = [desc[0] for desc in cur.description]
    hewan_list = []
    for row in cur.fetchall():
        hewan_dict = dict(zip(columns, row))
        hewan_dict['sudah_diadopsi'] = hewan_dict['id_adopter'] is not None
        hewan_list.append(hewan_dict)
    cur.close()
    conn.close()
    return hewan_list

# Fungsi pembantu untuk ambil data pengguna
def get_pengguna_data(username):
    conn = psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT']
    )
    cur = conn.cursor()
    # Ambil semua kolom yang relevan dari tabel pengguna
    cur.execute("SELECT username, email, nama_depan, nama_belakang, no_telepon FROM SIZOPI.pengguna WHERE username = %s", (username,))
    pengguna = cur.fetchone()
    cur.close()
    conn.close()
    if pengguna:
         # Sesuaikan nama kolom sesuai dengan urutan di query SELECT
         pengguna_columns = ['username', 'email', 'nama_depan', 'nama_belakang', 'no_telepon']
         return dict(zip(pengguna_columns, pengguna))
    return None


def cek_adopter(request):
    if request.method == "POST":
        username = request.POST.get("username")
        tipe = request.POST.get("tipe")
        id_hewan = request.POST.get("id_hewan")
        
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cur = conn.cursor()
        
        # Hanya cek di tabel pengguna
        cur.execute("SELECT username FROM SIZOPI.pengguna WHERE username = %s", (username,))
        pengguna = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if pengguna:
            # Jika user ada di pengguna, tampilkan form adopsi lengkap
            return redirect(f'/adoption/?show_adopter_form=True&username={username}&tipe={tipe}&id_hewan={id_hewan}')
        else:
            # Jika user belum ada di pengguna, tampilkan form registrasi user baru
            return redirect(f'/adoption/?show_user_registration=True&username={username}&tipe={tipe}&id_hewan={id_hewan}')

    return redirect('adoption_management:manage_adopt')

@csrf_exempt
def update_adopter_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            id_hewan = data.get("id_hewan")
            new_status = data.get("new_status")
            nominal = data.get("nominal")

            print(f"Debug - Data received: username={username}, id_hewan={id_hewan}, new_status={new_status}, nominal={nominal}")

            if not all([username, id_hewan, new_status is not None, nominal is not None]):
                return JsonResponse({"success": False, "error": "Data tidak lengkap."}, status=400)

            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cur = conn.cursor()

            # Cari id_adopter berdasarkan username
            cur.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", (username,))
            adopter_result = cur.fetchone()

            if not adopter_result:
                cur.close()
                conn.close()
                return JsonResponse({"success": False, "error": "Adopter tidak ditemukan."}, status=404)

            id_adopter = adopter_result[0]
            print(f"Debug - Found adopter_id: {id_adopter}")

            # Update status_pembayaran di tabel adopsi untuk row dengan tanggal berakhir terbaru
            cur.execute("""
                UPDATE SIZOPI.adopsi 
                SET status_pembayaran = %s 
                WHERE id_hewan = %s 
                AND id_adopter = %s 
                AND tgl_berhenti_adopsi = (
                    SELECT MAX(tgl_berhenti_adopsi) 
                    FROM SIZOPI.adopsi 
                    WHERE id_hewan = %s 
                    AND id_adopter = %s
                )
            """, (new_status, id_hewan, id_adopter, id_hewan, id_adopter))
            print(f"Debug - Updated adopsi status to {new_status}")

            conn.commit()
            print("Debug - Changes committed to database")

            cur.close()
            conn.close()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Debug - Error occurred: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)


@csrf_exempt
def stop_adoption(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_hewan = data.get("id_hewan")

            print(f"Debug - Stop adoption data received: id_hewan={id_hewan}")

            if not id_hewan:
                return JsonResponse({"success": False, "error": "ID Hewan tidak disediakan."}, status=400)

            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cur = conn.cursor()

            # Hapus semua data adopsi untuk hewan ini
            cur.execute(
                "DELETE FROM SIZOPI.adopsi WHERE id_hewan = %s",
                (id_hewan,)
            )
            print(f"Debug - Deleted all adoption records for hewan_id={id_hewan}")

            conn.commit()
            print("Debug - Changes committed to database")
            
            cur.close()
            conn.close()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Debug - Error occurred: {str(e)}")
            if 'conn' in locals() and conn:
                conn.rollback()
            if 'cur' in locals() and cur:
                cur.close()
            if 'conn' in locals() and conn:
                conn.close()
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@csrf_exempt
def delete_adopter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_adopter = data.get("id_adopter")

            print(f"Debug - Delete adopter data received: id_adopter={id_adopter}")

            if not id_adopter:
                return JsonResponse({"success": False, "error": "ID Adopter tidak disediakan."}, status=400)

            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cur = conn.cursor()

            cur.execute("""
                SELECT COUNT(*)
                FROM SIZOPI.adopsi
                WHERE id_adopter = %s AND tgl_berhenti_adopsi > CURRENT_DATE
            """, (id_adopter,))

            ongoing_adoptions_count = cur.fetchone()[0]
            print(f"Debug - Ongoing adoptions count: {ongoing_adoptions_count}")

            if ongoing_adoptions_count > 0:
                cur.close()
                conn.close()
                return JsonResponse({"success": False, "error": "Tidak dapat menghapus adopter karena masih memiliki adopsi yang sedang berlangsung."}, status=400)

            cur.execute("DELETE FROM SIZOPI.adopter WHERE id_adopter = %s", (id_adopter,))
            print(f"Debug - Deleted adopter with id: {id_adopter}")

            conn.commit()
            print("Debug - Changes committed to database")

            cur.close()
            conn.close()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Debug - Error occurred: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@csrf_exempt # Izinkan POST request tanpa CSRF token (untuk Fetch API)
def proses_perpanjang_adopsi(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_hewan = data.get('id_hewan')
            id_adopter = data.get('id_adopter')
            nominal = data.get('nominal')
            periode = data.get('periode') # dalam bulan

            print(f"Debug - Perpanjangan data received: hewan={id_hewan}, adopter={id_adopter}, nominal={nominal}, periode={periode}")

            if not all([id_hewan, id_adopter, nominal is not None, periode is not None]):
                return JsonResponse({"success": False, "error": "Data tidak lengkap."}, status=400)
            
            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cur = conn.cursor()

            # 1. Cari tanggal berakhir adopsi saat ini untuk hewan dan adopter ini
            cur.execute("SELECT tgl_berhenti_adopsi FROM SIZOPI.adopsi WHERE id_hewan = %s AND id_adopter = %s ORDER BY tgl_berhenti_adopsi DESC LIMIT 1", (id_hewan, id_adopter))
            current_adopsi_end_date_row = cur.fetchone()

            if not current_adopsi_end_date_row:
                 # Ini seharusnya tidak terjadi jika tombol perpanjang hanya muncul untuk adopsi yang ada
                 cur.close()
                 conn.close()
                 return JsonResponse({"success": False, "error": "Data adopsi saat ini tidak ditemukan."}, status=404)

            current_adopsi_end_date = current_adopsi_end_date_row[0]
            print(f"Debug - Current adopsi end date: {current_adopsi_end_date}")

            # 2. Hitung tanggal mulai dan tanggal berakhir baru
            # Tanggal mulai baru adalah sehari setelah tanggal berakhir adopsi saat ini
            new_start_date = current_adopsi_end_date + datetime.timedelta(days=1)

            # Hitung tanggal berakhir baru berdasarkan periode (kira-kira 30 hari per bulan)
            # Bisa disesuaikan dengan logika yang lebih tepat jika diperlukan
            days_periode = {3: 90, 6: 180, 12: 365}.get(periode, periode*30) # Fallback ke *30 jika nilai tidak standar
            new_end_date = new_start_date + datetime.timedelta(days=days_periode -1 ) # Kurangi 1 hari karena mulai inklusif
            print(f"Debug - New adopsi period: {new_start_date} to {new_end_date}")

            # 3. Sisipkan record adopsi baru
            cur.execute(
                "INSERT INTO SIZOPI.adopsi (id_adopter, id_hewan, tgl_mulai_adopsi, tgl_berhenti_adopsi, status_pembayaran, kontribusi_finansial) VALUES (%s, %s, %s, %s, %s, %s)",
                (id_adopter, id_hewan, new_start_date, new_end_date, 'Tertunda', nominal) # Status awal 'Tertunda'
            )
            print("Debug - New adopsi record inserted.")

            conn.commit()
            print("Debug - Changes committed to database.")
            
            cur.close()
            conn.close()

            # Trigger database akan otomatis mengupdate total_kontribusi saat status berubah

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Debug - Error occurred during perpanjangan: {str(e)}")
            if 'conn' in locals() and conn:
                conn.rollback()
            if 'cur' in locals() and cur:
                cur.close()
            if 'conn' in locals() and conn:
                conn.close()
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)