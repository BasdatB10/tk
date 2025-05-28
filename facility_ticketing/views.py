from django.shortcuts import render, redirect
import psycopg2
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from datetime import date, datetime

# Create your views here.
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

def reservasi_pengunjung(request):
    # Data atraksi untuk opsi dropdown (sama dengan data di manajemen_atraksi)
    atraksi_data = [
        {
            'nama': 'Taman Burung Tropis', 
            'lokasi': 'Area Tengah Kebun Binatang - Dekat Kafe', 
            'kapasitas': '50', 
            'jadwal': '2025-04-24 09:00:00', 
            'hewan': 'Harimau Sumatra', 
            'petugas': 'Andrew Tambunan'
        },
        {
            'nama': 'Aquaarium Laut Dalam', 
            'lokasi': 'Bangunan Akuarium - Area Laut Dalam', 
            'kapasitas': '80', 
            'jadwal': '2025-04-24 10:00:00', 
            'hewan': 'Penguin', 
            'petugas': 'Alfian Pratama'
        },
        {
            'nama': 'Kawasan Panda', 
            'lokasi': 'Area Panda - Tempat Pandas Makan', 
            'kapasitas': '60', 
            'jadwal': '2025-04-24 11:00:00', 
            'hewan': 'Panda Raksasa', 
            'petugas': 'Rebecca Novita'
        },
        {
            'nama': 'Kereta Gantung Savana', 
            'lokasi': 'Atas Area Savana - Jalur Udara', 
            'kapasitas': '40', 
            'jadwal': '2025-04-24 12:00:00', 
            'hewan': '-', 
            'petugas': 'Diana Rahmawati'
        },
        {
            'nama': 'Kebun Kaktus Eksotik', 
            'lokasi': 'Dekat Taman Gajah', 
            'kapasitas': '30', 
            'jadwal': '2025-04-24 13:00:00', 
            'hewan': '-', 
            'petugas': 'Felix Aditya'
        },
        {
            'nama': 'Teater Satwa Malam', 
            'lokasi': 'Gedung Pertunjukan - Area Malam', 
            'kapasitas': '100', 
            'jadwal': '2025-04-24 14:00:00', 
            'hewan': '-', 
            'petugas': 'Victor Lukman'
        },
        {
            'nama': 'Jembatan Gantung Safari', 
            'lokasi': 'Tengah Safari Hutan', 
            'kapasitas': '35', 
            'jadwal': '2025-04-24 15:00:00', 
            'hewan': '-', 
            'petugas': 'Toni Setiawan'
        },
        {
            'nama': 'Taman Reptil Tropis', 
            'lokasi': 'Sebelah Kandang Ular dan Komodo', 
            'kapasitas': '45', 
            'jadwal': '2025-04-24 16:00:00', 
            'hewan': '-', 
            'petugas': 'Bella Silviana'
        }
    ]
    
    # Data wahana untuk opsi dropdown tambahan
    wahana_data = [
        {
            'nama': 'Safari Jeep',
            'lokasi': 'Area Safari Utama',
            'kapasitas': '30',
            'jadwal': '2025-04-24 10:30:00',
            'peraturan': 'Pengunjung diharapkan mengenakan sabuk pengaman sepanjang perjalanan.'
        },
        {
            'nama': 'Panggung Pertunjukan Gajah',
            'lokasi': 'Arena Pertunjukan Utama',
            'kapasitas': '100',
            'jadwal': '2025-04-24 14:00:00',
            'peraturan': 'Pengunjung dilarang mendekat ke panggung selama pertunjukan.'
        },
        {
            'nama': 'Balon Udara Edukasi',
            'lokasi': 'Taman Tengah',
            'kapasitas': '20',
            'jadwal': '2025-04-24 09:00:00',
            'peraturan': 'Anak-anak harus didampingi orang tua.'
        },
        {
            'nama': 'Zona Interaktif Serangga',
            'lokasi': 'Rumah Serangga',
            'kapasitas': '40',
            'jadwal': '2025-04-24 13:00:00',
            'peraturan': 'Dilarang menyentuh serangga tanpa izin petugas.'
        },
        {
            'nama': 'Simulator Ekspedisi Kutub',
            'lokasi': 'Zona Kutub',
            'kapasitas': '25',
            'jadwal': '2025-04-24 15:00:00',
            'peraturan': 'Wajib menggunakan peralatan keselamatan yang disediakan.'
        }
    ]
    
    # Data reservasi pengunjung (dummy data)
    reservasi_data = [
        {
            'id': 1,
            'nama_atraksi': 'Taman Burung Tropis',
            'lokasi': 'Area Tengah Kebun Binatang - Dekat Kafe',
            'jam': '09:00',
            'tanggal': '2025-04-24',
            'jumlah_tiket': 3,
            'status': 'Terjadwal',
            'user_id': 'anggita.desmawati17',
        },
        {
            'id': 2,
            'nama_atraksi': 'Aquaarium Laut Dalam',
            'lokasi': 'Bangunan Akuarium - Area Laut Dalam',
            'jam': '10:00',
            'tanggal': '2025-04-25',
            'jumlah_tiket': 4,
            'status': 'Terjadwal',
            'user_id': 'anggita.desmawati17',
        },
        {
            'id': 3,
            'nama_atraksi': 'Safari Jeep',
            'lokasi': 'Area Safari Utama',
            'jam': '10:30',
            'tanggal': '2025-04-26',
            'jumlah_tiket': 2,
            'status': 'Terjadwal',
            'user_id': 'anggita.desmawati17',
        },
        {
            'id': 4,
            'nama_atraksi': 'Zona Interaktif Serangga',
            'lokasi': 'Rumah Serangga',
            'jam': '13:00',
            'tanggal': '2025-04-27',
            'jumlah_tiket': 5,
            'status': 'Terjadwal',
            'user_id': 'anggita.desmawati17',
        }
    ]
    
    # Gabungkan data atraksi dan wahana untuk fasilitas yang bisa direservasi
    fasilitas_data = atraksi_data + wahana_data
    
    context = {
        'atraksi_data': atraksi_data,
        'wahana_data': wahana_data,
        'reservasi_data': reservasi_data,
        'fasilitas_data': fasilitas_data
    }
    
    return render(request, 'reservasi_pengunjung.html', context)

def admin_reservasi(request):
    # Data reservasi untuk semua pengunjung (dengan username)
    all_reservasi_data = [
        {
            'id': 1,
            'username': 'anggita.desmawati17',
            'nama_pengunjung': 'Anggita Desmawati',
            'nama_atraksi': 'Taman Burung Tropis',
            'tanggal': '2025-04-24',
            'jam': '09:00',
            'jumlah_tiket': 3,
            'status': 'Terjadwal',
        },
        {
            'id': 2,
            'username': 'anggita.desmawati17',
            'nama_pengunjung': 'Anggita Desmawati',
            'nama_atraksi': 'Aquaarium Laut Dalam',
            'tanggal': '2025-04-25',
            'jam': '10:00',
            'jumlah_tiket': 4,
            'status': 'Terjadwal',
        },
        {
            'id': 3,
            'username': 'johndoe22',
            'nama_pengunjung': 'John Doe',
            'nama_atraksi': 'Safari Jeep',
            'tanggal': '2025-04-26',
            'jam': '10:30',
            'jumlah_tiket': 2,
            'status': 'Terjadwal',
        },
        {
            'id': 4,
            'username': 'maria.silva',
            'nama_pengunjung': 'Maria Silva',
            'nama_atraksi': 'Zona Interaktif Serangga',
            'tanggal': '2025-04-27',
            'jam': '13:00',
            'jumlah_tiket': 5,
            'status': 'Terjadwal',
        },
        {
            'id': 5,
            'username': 'robert.johnson',
            'nama_pengunjung': 'Robert Johnson',
            'nama_atraksi': 'Teater Satwa Malam',
            'tanggal': '2025-04-28',
            'jam': '14:00',
            'jumlah_tiket': 2,
            'status': 'Dibatalkan',
        },
        {
            'id': 6,
            'username': 'sarah.lee',
            'nama_pengunjung': 'Sarah Lee',
            'nama_atraksi': 'Kawasan Panda',
            'tanggal': '2025-04-30',
            'jam': '11:00',
            'jumlah_tiket': 3,
            'status': 'Terjadwal',
        }
    ]
    
    return render(request, 'admin_reservasi.html', {'reservasi_data': all_reservasi_data})

@csrf_exempt
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