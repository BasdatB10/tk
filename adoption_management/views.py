from django.shortcuts import render, redirect
import psycopg2
from django.conf import settings
import uuid
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.http import JsonResponse
import json


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
                        # Gabungkan dengan data pengunjung (alamat) - asumsi organisasi juga punya alamat di pengunjung
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
        "pengguna_data": pengguna_data, # Teruskan data pengguna jika ditemukan
        "adopter_specific_data": adopter_specific_data # Teruskan data adopter spesifik jika ditemukan
    })


def show_adopter_page(request):
    return render(request,"adopter_page.html")

def show_adopter_list(request):
    return render(request,"adopter_list.html")

def daftar_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        nama_depan = request.POST.get("nama_depan")
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
            # Insert ke pengguna
            cur.execute(
                "INSERT INTO SIZOPI.pengguna (username, email, password, nama_depan, nama_belakang, no_telepon) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, email, password, nama_depan, nama_belakang, no_telepon)
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
        LEFT JOIN SIZOPI.adopsi a
            ON h.id = a.id_hewan
        LEFT JOIN SIZOPI.adopter ad
            ON a.id_adopter = ad.id_adopter
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

            # 1. Cari id_adopter berdasarkan username
            cur.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", (username,))
            adopter_result = cur.fetchone()

            if not adopter_result:
                cur.close()
                conn.close()
                return JsonResponse({"success": False, "error": "Adopter tidak ditemukan."}, status=404)

            id_adopter = adopter_result[0]
            print(f"Debug - Found adopter_id: {id_adopter}")

            # 2. Update status_pembayaran di tabel adopsi
            cur.execute(
                "UPDATE SIZOPI.adopsi SET status_pembayaran = %s WHERE id_hewan = %s AND id_adopter = %s",
                (new_status, id_hewan, id_adopter)
            )
            print(f"Debug - Updated adopsi status to {new_status}")

            # 3. Update total_kontribusi jika status adalah 'lunas'
            if new_status == 'lunas':
                # Cek total kontribusi saat ini
                cur.execute("SELECT total_kontribusi FROM SIZOPI.adopter WHERE id_adopter = %s", (id_adopter,))
                current_total = cur.fetchone()[0] or 0
                print(f"Debug - Current total kontribusi: {current_total}")
                
                # Update total kontribusi
                new_total = current_total + nominal
                print(f"Debug - New total kontribusi will be: {new_total}")
                
                cur.execute(
                    "UPDATE SIZOPI.adopter SET total_kontribusi = %s WHERE id_adopter = %s",
                    (new_total, id_adopter)
                )
                print(f"Debug - Updated total kontribusi to {new_total}")

            conn.commit()
            print("Debug - Changes committed to database")
            
            cur.close()
            conn.close()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Debug - Error occurred: {str(e)}")
            conn.rollback()
            if 'cur' in locals() and cur:
                cur.close()
            if 'conn' in locals() and conn:
                conn.close()
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@csrf_exempt
def stop_adoption(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            id_hewan = data.get("id_hewan")

            print(f"Debug - Stop adoption data received: username={username}, id_hewan={id_hewan}")

            if not all([username, id_hewan]):
                return JsonResponse({"success": False, "error": "Data tidak lengkap."}, status=400)

            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cur = conn.cursor()

            # 1. Cari id_adopter berdasarkan username
            cur.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", (username,))
            adopter_result = cur.fetchone()

            if not adopter_result:
                cur.close()
                conn.close()
                return JsonResponse({"success": False, "error": "Adopter tidak ditemukan."}, status=404)

            id_adopter = adopter_result[0]
            print(f"Debug - Found adopter_id: {id_adopter}")

            # 2. Hapus data adopsi berdasarkan id_hewan dan id_adopter
            cur.execute(
                "DELETE FROM SIZOPI.adopsi WHERE id_hewan = %s AND id_adopter = %s",
                (id_hewan, id_adopter)
            )
            print(f"Debug - Deleted adoption record for hewan_id={id_hewan} and adopter_id={id_adopter}")

            conn.commit()
            print("Debug - Changes committed to database")
            
            cur.close()
            conn.close()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Debug - Error occurred: {str(e)}")
            conn.rollback()
            if 'cur' in locals() and cur:
                cur.close()
            if 'conn' in locals() and conn:
                conn.close()
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)