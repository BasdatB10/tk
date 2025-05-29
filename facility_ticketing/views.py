from django.shortcuts import render, redirect
import psycopg2
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from datetime import date, datetime
from django.http import JsonResponse
from base.views import session_required
import os
from functools import wraps
from django.contrib import messages

# Create your views here.
def pengunjung_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('base:home')
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
            cursor.execute("""
                SELECT username_P FROM PENGUNJUNG WHERE username_P = %s
            """, (request.session.get('username'),))
            pengunjung = cursor.fetchone()
            cursor.close()
            conn.close()
            if not pengunjung:
                return redirect('base:dashboard')
        except Exception as e:
            messages.error(request, f'Error checking user role: {str(e)}')
            return redirect('base:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('base:home')
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
            cursor.execute("""
                SELECT username_sa FROM STAF_ADMIN WHERE username_sa = %s
            """, (request.session.get('username'),))
            admin = cursor.fetchone()
            cursor.close()
            conn.close()
            if not admin:
                return redirect('base:dashboard')
        except Exception as e:
            messages.error(request, f'Error checking user role: {str(e)}')
            return redirect('base:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manajemen_atraksi(request):
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO sizopi;")

        # Ambil data atraksi
        cursor.execute('''
            SELECT 
                f.nama, 
                a.lokasi, 
                f.kapasitas_max, 
                f.jadwal,
                -- Gabungkan nama hewan yang terlibat
                COALESCE(string_agg(DISTINCT h.nama, ', '), '-') AS hewan,
                -- Gabungkan nama petugas (distinct) yang bertugas di atraksi ini
                COALESCE(string_agg(DISTINCT pengguna.nama_depan || ' ' || pengguna.nama_belakang, ', '), '-') AS petugas
            FROM fasilitas f
            JOIN atraksi a ON f.nama = a.nama_atraksi
            LEFT JOIN berpartisipasi bp ON f.nama = bp.nama_fasilitas
            LEFT JOIN hewan h ON bp.id_hewan = h.id
            LEFT JOIN jadwal_penugasan jp ON jp.nama_atraksi = f.nama
            LEFT JOIN pelatih_hewan ph ON jp.username_lh = ph.username_lh
            LEFT JOIN pengguna ON ph.username_lh = pengguna.username
            GROUP BY f.nama, a.lokasi, f.kapasitas_max, f.jadwal
            ORDER BY f.jadwal ASC
        ''')
        rows = cursor.fetchall()
        atraksi_data = []
        for row in rows:
            atraksi_data.append({
                'nama': row[0],
                'lokasi': row[1],
                'kapasitas': row[2],
                'jadwal': str(row[3]),
                'hewan': row[4],
                'petugas': row[5],
            })

        # Ambil daftar hewan
        cursor.execute("SELECT id, nama FROM hewan ORDER BY nama")
        hewan_list = cursor.fetchall()
        # Ambil daftar petugas
        cursor.execute("SELECT pengguna.username, pengguna.nama_depan || ' ' || pengguna.nama_belakang FROM pelatih_hewan JOIN pengguna ON pelatih_hewan.username_lh = pengguna.username ORDER BY pengguna.nama_depan")
        petugas_list = cursor.fetchall()
        cursor.close()
        conn.close()
        return render(request, 'manajemen_atraksi.html', {'atraksi_data': atraksi_data, 'hewan_list': hewan_list, 'petugas_list': petugas_list})
    except Exception as e:
        return render(request, 'manajemen_atraksi.html', {'atraksi_data': [], 'hewan_list': [], 'petugas_list': [], 'error': str(e)})


def manajemen_wahana(request):
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO sizopi;")

        # Ambil data wahana, peraturan dari tabel wahana
        cursor.execute('''
            SELECT 
                f.nama, 
                f.kapasitas_max, 
                f.jadwal,
                w.peraturan
            FROM fasilitas f
            JOIN wahana w ON f.nama = w.nama_wahana
            ORDER BY f.jadwal ASC
        ''')
        rows = cursor.fetchall()
        wahana_data = []
        for row in rows:
            wahana_data.append({
                'nama': row[0],
                'kapasitas': row[1],
                'jadwal': str(row[2]),
                'peraturan': row[3] if row[3] else '-'
            })

        cursor.close()
        conn.close()
        return render(request, 'manajemen_wahana.html', {'wahana_data': wahana_data})
    except Exception as e:
        print('Error:', e)
        return render(request, 'manajemen_wahana.html', {'wahana_data': [], 'error': str(e)})

@session_required
@pengunjung_required
def reservasi_pengunjung_list_fasilitas(request):
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO sizopi;")
        # Ambil semua fasilitas (atraksi + wahana) dan kapasitas tersisa
        cursor.execute('''
            SELECT f.nama, 
                   CASE WHEN a.nama_atraksi IS NOT NULL THEN 'Atraksi' ELSE 'Wahana' END AS jenis,
                   f.jadwal, 
                   f.kapasitas_max,
                   COALESCE((
                       SELECT f.kapasitas_max - SUM(r.jumlah_tiket)
                       FROM reservasi r
                       WHERE r.nama_fasilitas = f.nama AND r.tanggal_kunjungan = CURRENT_DATE AND r.status != 'Dibatalkan'
                   ), f.kapasitas_max) AS kapasitas_tersedia
            FROM fasilitas f
            LEFT JOIN atraksi a ON f.nama = a.nama_atraksi
            LEFT JOIN wahana w ON f.nama = w.nama_wahana
            ORDER BY f.jadwal ASC
        ''')
        fasilitas_data = []
        for row in cursor.fetchall():
            fasilitas_data.append({
                'nama': row[0],
                'jenis': row[1],
                'jadwal': str(row[2]),
                'kapasitas_max': row[3],
                'kapasitas_tersedia': row[4],
            })
        cursor.close()
        conn.close()
        return render(request, 'reservasi_pengunjung_list_fasilitas.html', {'fasilitas_data': fasilitas_data})
    except Exception as e:
        return render(request, 'reservasi_pengunjung_list_fasilitas.html', {'fasilitas_data': [], 'error': str(e)})

@csrf_exempt
@session_required
@pengunjung_required
def tambah_reservasi_pengunjung(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            username = request.session['username']
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
            jumlah_tiket = request.POST.get('jumlah_tiket')
            # Default status: Menunggu Pembayaran
            cursor.execute('''
                INSERT INTO reservasi (username_p, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, 'Menunggu Pembayaran'))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Tambah reservasi error:', e)
        return redirect('facility_ticketing:reservasi_pengunjung_riwayat')
    return redirect('facility_ticketing:reservasi_pengunjung_list_fasilitas')

@session_required
@pengunjung_required
def reservasi_pengunjung_riwayat(request):
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO sizopi;")
        username = request.session['username']
        cursor.execute('''
            SELECT nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status
            FROM reservasi
            WHERE username_p = %s
            ORDER BY tanggal_kunjungan DESC
        ''', (username,))
        reservasi_data = []
        for row in cursor.fetchall():
            reservasi_data.append({
                'nama_fasilitas': row[0],
                'tanggal_kunjungan': row[1],
                'jumlah_tiket': row[2],
                'status': row[3],
            })
        cursor.close()
        conn.close()
        return render(request, 'reservasi_pengunjung_riwayat.html', {'reservasi_data': reservasi_data})
    except Exception as e:
        return render(request, 'reservasi_pengunjung_riwayat.html', {'reservasi_data': [], 'error': str(e)})

@csrf_exempt
@session_required
@pengunjung_required
def edit_reservasi_pengunjung(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            username = request.session['username']
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
            jumlah_tiket = request.POST.get('jumlah_tiket')
            cursor.execute('''
                UPDATE reservasi SET jumlah_tiket = %s
                WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
            ''', (jumlah_tiket, username, nama_fasilitas, tanggal_kunjungan))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Edit reservasi error:', e)
        return redirect('facility_ticketing:reservasi_pengunjung_riwayat')
    return redirect('facility_ticketing:reservasi_pengunjung_riwayat')

@csrf_exempt
@session_required
@pengunjung_required
def batal_reservasi_pengunjung(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            username = request.session['username']
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
            cursor.execute('''
                UPDATE reservasi SET status = 'Dibatalkan'
                WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
            ''', (username, nama_fasilitas, tanggal_kunjungan))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Batal reservasi error:', e)
        return redirect('facility_ticketing:reservasi_pengunjung_riwayat')
    return redirect('facility_ticketing:reservasi_pengunjung_riwayat')

@csrf_exempt
@session_required
@admin_required
def admin_reservasi(request):
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO sizopi;")

        # Ambil data reservasi
        cursor.execute('''
            SELECT 
                username_p,
                nama_fasilitas,
                tanggal_kunjungan,
                jumlah_tiket,
                status
            FROM reservasi
            ORDER BY tanggal_kunjungan DESC
        ''')
        rows = cursor.fetchall()
        reservasi_data = []
        for row in rows:
            reservasi_data.append({
                'username': row[0],
                'nama_fasilitas': row[1],
                'tanggal_kunjungan': row[2],
                'jumlah_tiket': row[3],
                'status': row[4]
            })

        cursor.close()
        conn.close()
        return render(request, 'admin_reservasi.html', {'reservasi_data': reservasi_data})
    except Exception as e:
        print('Error:', e)
        return render(request, 'admin_reservasi.html', {'reservasi_data': [], 'error': str(e)})
    
@csrf_exempt
@session_required
@admin_required
def update_status_reservasi(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            
            username = request.POST.get('username')
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
            status = request.POST.get('status')
            
            if status not in ['Menunggu Pembayaran', 'Konfirmasi', 'Dibatalkan']:
                return JsonResponse({'status': 'error', 'message': 'Status tidak valid'})
            
            cursor.execute("""
                UPDATE reservasi 
                SET status = %s
                WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
            """, (status, username, nama_fasilitas, tanggal_kunjungan))
            
            conn.commit()
            cursor.close()
            conn.close()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print('Error:', e)
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
@session_required
@admin_required
def batalkan_reservasi(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            
            username = request.POST.get('username')
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
            
            cursor.execute("""
                UPDATE reservasi 
                SET status = 'Dibatalkan'
                WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
            """, (username, nama_fasilitas, tanggal_kunjungan))
            
            conn.commit()
            cursor.close()
            conn.close()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print('Error:', e)
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
@session_required
@admin_required
def tambah_atraksi(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            nama = request.POST.get('nama_atraksi')
            lokasi = request.POST.get('lokasi')
            kapasitas = request.POST.get('kapasitas')
            jadwal_input = request.POST.get('jadwal')
            jadwal_full = f"{date.today()} {jadwal_input}:00" if jadwal_input else None
            petugas = request.POST.get('petugas')
            hewan_list = request.POST.getlist('hewan')
            # Insert ke fasilitas
            cursor.execute("INSERT INTO fasilitas (nama, kapasitas_max, jadwal) VALUES (%s, %s, %s)", (nama, kapasitas, jadwal_full))
            # Insert ke atraksi
            cursor.execute("INSERT INTO atraksi (nama_atraksi, lokasi) VALUES (%s, %s)", (nama, lokasi))
            # Insert ke jadwal_penugasan
            if petugas:
                cursor.execute("INSERT INTO jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi) VALUES (%s, CURRENT_DATE, %s)", (petugas, nama))
            # Insert ke berpartisipasi untuk setiap hewan
            for hewan_id in hewan_list:
                cursor.execute("INSERT INTO berpartisipasi (nama_fasilitas, id_hewan) VALUES (%s, %s)", (nama, hewan_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Tambah atraksi error:', e)
        return redirect('facility_ticketing:manajemen_atraksi')
    return redirect('facility_ticketing:manajemen_atraksi')

@csrf_exempt
@session_required
@admin_required
def edit_atraksi(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            nama = request.POST.get('nama_atraksi')
            lokasi = request.POST.get('lokasi')
            kapasitas = request.POST.get('kapasitas')
            jadwal_input = request.POST.get('jadwal')
            jadwal_full = f"{date.today()} {jadwal_input}:00" if jadwal_input else None
            petugas = request.POST.get('petugas')
            hewan_list = request.POST.getlist('hewan')
            # Update fasilitas
            cursor.execute("UPDATE fasilitas SET kapasitas_max=%s, jadwal=%s WHERE nama=%s", (kapasitas, jadwal_full, nama))
            # Update atraksi
            cursor.execute("UPDATE atraksi SET lokasi=%s WHERE nama_atraksi=%s", (lokasi, nama))
            # Update jadwal_penugasan hanya jika ada petugas baru
            if petugas:
                cursor.execute("DELETE FROM jadwal_penugasan WHERE nama_atraksi=%s", (nama,))
                cursor.execute("INSERT INTO jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi) VALUES (%s, CURRENT_DATE, %s)", (petugas, nama))
            # Update berpartisipasi hanya jika ada hewan baru
            if hewan_list:
                cursor.execute("DELETE FROM berpartisipasi WHERE nama_fasilitas=%s", (nama,))
                for hewan_id in hewan_list:
                    cursor.execute("INSERT INTO berpartisipasi (nama_fasilitas, id_hewan) VALUES (%s, %s)", (nama, hewan_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Edit atraksi error:', e)
        return redirect('facility_ticketing:manajemen_atraksi')
    return redirect('facility_ticketing:manajemen_atraksi')

@csrf_exempt
@session_required
@admin_required
def hapus_atraksi(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            nama = request.POST.get('nama_atraksi')
            cursor.execute("DELETE FROM berpartisipasi WHERE nama_fasilitas=%s", (nama,))
            cursor.execute("DELETE FROM jadwal_penugasan WHERE nama_atraksi=%s", (nama,))
            cursor.execute("DELETE FROM atraksi WHERE nama_atraksi=%s", (nama,))
            cursor.execute("DELETE FROM fasilitas WHERE nama=%s", (nama,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Hapus atraksi error:', e)
        return redirect('facility_ticketing:manajemen_atraksi')
    return redirect('facility_ticketing:manajemen_atraksi')

@csrf_exempt
@session_required
@admin_required
def tambah_wahana(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            nama = request.POST.get('nama_wahana')
            kapasitas = request.POST.get('kapasitas')
            jadwal_input = request.POST.get('jadwal')
            jadwal_full = f"{date.today()} {jadwal_input}:00" if jadwal_input else None
            peraturan = request.POST.get('peraturan')
            # Insert ke fasilitas (tanpa peraturan)
            cursor.execute("INSERT INTO fasilitas (nama, kapasitas_max, jadwal) VALUES (%s, %s, %s)", 
                         (nama, kapasitas, jadwal_full))
            # Insert ke wahana (peraturan masuk ke sini)
            cursor.execute("INSERT INTO wahana (nama_wahana, peraturan) VALUES (%s, %s)", (nama, peraturan))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Tambah wahana error:', e)
        return redirect('facility_ticketing:manajemen_wahana')
    return redirect('facility_ticketing:manajemen_wahana')

@csrf_exempt
@session_required
@admin_required
def edit_wahana(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            nama = request.POST.get('nama_wahana')
            kapasitas = request.POST.get('kapasitas')
            jadwal_input = request.POST.get('jadwal')
            jadwal_full = f"{date.today()} {jadwal_input}:00" if jadwal_input else None
            # Tidak update peraturan!
            cursor.execute("UPDATE fasilitas SET kapasitas_max=%s, jadwal=%s WHERE nama=%s", 
                         (kapasitas, jadwal_full, nama))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Edit wahana error:', e)
        return redirect('facility_ticketing:manajemen_wahana')
    return redirect('facility_ticketing:manajemen_wahana')

@csrf_exempt
@session_required
@admin_required
def hapus_wahana(request):
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                database=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            cursor.execute("SET search_path TO sizopi;")
            nama = request.POST.get('nama_wahana')
            cursor.execute("DELETE FROM wahana WHERE nama_wahana=%s", (nama,))
            cursor.execute("DELETE FROM fasilitas WHERE nama=%s", (nama,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Hapus wahana error:', e)
        return redirect('facility_ticketing:manajemen_wahana')
    return redirect('facility_ticketing:manajemen_wahana')

@session_required
@admin_required
def kelola_pengunjung(request):
    return render(request, 'kelola_pengunjung.html')