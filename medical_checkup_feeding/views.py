from django.shortcuts import render, redirect
import json, uuid, psycopg2, os, dotenv
from django.conf import settings
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
dotenv.load_dotenv()

def session_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('base:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def dokter_hewan_required(view_func):
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
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            dokter_hewan = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not dokter_hewan:
                return redirect('base:dashboard')
                
        except Exception as e:
            messages.error(request, f'Error checking user role: {str(e)}')
            return redirect('base:dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def penjaga_hewan_required(view_func):
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
                SELECT username_jh FROM PENJAGA_HEWAN WHERE username_jh = %s
            """, (request.session.get('username'),))
            
            penjaga_hewan = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not penjaga_hewan:
                return redirect('base:dashboard')
                
        except Exception as e:
            messages.error(request, f'Error checking user role: {str(e)}')
            return redirect('base:dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@dokter_hewan_required
def medical_record(request):
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
            SELECT 
                cm.id_hewan,
                cm.username_dh,
                cm.tanggal_pemeriksaan,
                cm.diagnosis,
                cm.pengobatan,
                cm.status_kesehatan,
                cm.catatan_tindak_lanjut,
                h.nama as nama_hewan,
                h.spesies,
                p.nama_depan || ' ' || p.nama_belakang as nama_dokter
            FROM CATATAN_MEDIS cm
            JOIN HEWAN h ON cm.id_hewan = h.id
            JOIN DOKTER_HEWAN dh ON cm.username_dh = dh.username_DH
            JOIN PENGGUNA p ON dh.username_DH = p.username
            ORDER BY cm.tanggal_pemeriksaan DESC
        """)
        
        medical_records = cursor.fetchall()
      
        cursor.execute("""
            SELECT id, nama, spesies, status_kesehatan
            FROM HEWAN
            ORDER BY nama
        """)
        
        animals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = {
            'medical_records': medical_records,
            'animals': animals,
        }
        
        return render(request, 'medical_record.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading medical records: {str(e)}')
        return render(request, 'medical_record.html', {'medical_records': [], 'animals': []})

@dokter_hewan_required
def add_medical_record(request):
    """View untuk menambah rekam medis baru"""
    if request.method == 'POST':
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
            
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
            status_kesehatan = request.POST.get('status_kesehatan')
            diagnosis = request.POST.get('diagnosis', '')
            pengobatan = request.POST.get('pengobatan', '')

            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menambah rekam medis.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_record')
            
            cursor.execute("SET client_min_messages TO NOTICE;")
            
            cursor.execute("""
                INSERT INTO CATATAN_MEDIS 
                (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_hewan,
                request.session.get('username'),
                tanggal_pemeriksaan,
                diagnosis if diagnosis else None,
                pengobatan if pengobatan else None,
                status_kesehatan,
                None 
            ))

            cursor.execute("""
                UPDATE HEWAN 
                SET status_kesehatan = %s 
                WHERE id = %s
            """, (status_kesehatan, id_hewan))

            for notice in conn.notices:
                if 'SUKSES:' in notice:
                    messages.success(request, notice.strip())
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Rekam medis berhasil ditambahkan!')
            return redirect('medical_checkup_feeding:medical_record')
            
        except Exception as e:
            messages.error(request, f'Error adding medical record: {str(e)}')
            return redirect('medical_checkup_feeding:medical_record')

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
            SELECT id, nama, spesies, status_kesehatan
            FROM HEWAN
            ORDER BY nama
        """)
        
        animals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = {
            'animals': animals,
        }
        
        return render(request, 'add_medical_record.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading form: {str(e)}')
        return redirect('medical_checkup_feeding:medical_record')

@dokter_hewan_required
def edit_medical_record(request, id_hewan, tanggal_pemeriksaan):
    """View untuk mengedit rekam medis (hanya untuk hewan yang sakit)"""
    if request.method == 'POST':
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
            
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut', '')
            diagnosis_baru = request.POST.get('diagnosis_baru', '')
            pengobatan_baru = request.POST.get('pengobatan_baru', '')
            
            # Update rekam medis dengan dokter yang sedang login
            cursor.execute("""
                UPDATE CATATAN_MEDIS 
                SET catatan_tindak_lanjut = %s,
                    diagnosis = COALESCE(NULLIF(%s, ''), diagnosis),
                    pengobatan = COALESCE(NULLIF(%s, ''), pengobatan),
                    username_dh = %s
                WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
            """, (
                catatan_tindak_lanjut if catatan_tindak_lanjut else None,
                diagnosis_baru,
                pengobatan_baru,
                request.session.get('username'),  # Update dengan dokter yang sedang login
                id_hewan,
                tanggal_pemeriksaan
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Rekam medis berhasil diperbarui!')
            return redirect('medical_checkup_feeding:medical_record')
            
        except Exception as e:
            messages.error(request, f'Error updating medical record: {str(e)}')
            return redirect('medical_checkup_feeding:medical_record')
    
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
            SELECT 
                cm.id_hewan,
                cm.username_dh,
                cm.tanggal_pemeriksaan,
                cm.diagnosis,
                cm.pengobatan,
                cm.status_kesehatan,
                cm.catatan_tindak_lanjut,
                h.nama as nama_hewan,
                h.status_kesehatan as status_hewan_saat_ini,
                p.nama_depan || ' ' || p.nama_belakang as nama_dokter_asli
            FROM CATATAN_MEDIS cm
            JOIN HEWAN h ON cm.id_hewan = h.id
            JOIN DOKTER_HEWAN dh ON cm.username_dh = dh.username_DH
            JOIN PENGGUNA p ON dh.username_DH = p.username
            WHERE cm.id_hewan = %s AND cm.tanggal_pemeriksaan = %s
        """, (id_hewan, tanggal_pemeriksaan))
        
        medical_record = cursor.fetchone()
        
        if not medical_record:
            messages.error(request, 'Rekam medis tidak ditemukan.')
            cursor.close()
            conn.close()
            return redirect('medical_checkup_feeding:medical_record')
        
        if medical_record[8] != 'Sakit': 
            messages.error(request, 'Rekam medis hanya dapat diedit untuk hewan yang sakit.')
            cursor.close()
            conn.close()
            return redirect('medical_checkup_feeding:medical_record')
        
        cursor.close()
        conn.close()
        
        context = {
            'medical_record': medical_record,
        }
        
        return render(request, 'edit_medical_record.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading medical record: {str(e)}')
        return redirect('medical_checkup_feeding:medical_record')

@dokter_hewan_required
def delete_medical_record(request, id_hewan, tanggal_pemeriksaan):
    """View untuk menghapus rekam medis"""
    if request.method == 'POST':
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
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menghapus rekam medis.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_record')
            cursor.execute("""
                DELETE FROM CATATAN_MEDIS 
                WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
            """, (id_hewan, tanggal_pemeriksaan))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Rekam medis berhasil dihapus!')
            
        except Exception as e:
            messages.error(request, f'Error deleting medical record: {str(e)}')
    
    return redirect('medical_checkup_feeding:medical_record')

@dokter_hewan_required
def medical_checkup(request):
    """View untuk menampilkan jadwal pemeriksaan kesehatan"""
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
            SELECT 
                h.id,
                h.nama,
                h.spesies,
                h.status_kesehatan,
                h.nama_habitat,
                jpk.tgl_pemeriksaan_selanjutnya,
                jpk.freq_pemeriksaan_rutin
            FROM HEWAN h
            LEFT JOIN JADWAL_PEMERIKSAAN_KESEHATAN jpk ON h.id = jpk.id_hewan
            ORDER BY h.nama
        """)
        
        animals_with_schedules = cursor.fetchall()
        animals = {}
        for row in animals_with_schedules:
            animal_id = str(row[0])
            if animal_id not in animals:
                animals[animal_id] = {
                    'id': animal_id,
                    'nama': row[1],
                    'spesies': row[2],
                    'status_kesehatan': row[3],
                    'nama_habitat': row[4],
                    'schedules': [],
                    'frequency': None
                }
            
            if row[5]: 
                animals[animal_id]['schedules'].append({
                    'tanggal': row[5],
                    'frequency': row[6]
                })
                if not animals[animal_id]['frequency']:
                    animals[animal_id]['frequency'] = row[6]
        
        cursor.close()
        conn.close()
        
        context = {
            'animals_data': animals,
        }
        
        return render(request, 'medical_checkup.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading medical checkup schedule: {str(e)}')
        return render(request, 'medical_checkup.html', {'animals_data': {}})
    
@dokter_hewan_required
def add_checkup_schedule(request):
    """View untuk menambah jadwal pemeriksaan kesehatan baru"""
    if request.method == 'POST':
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
            
            id_hewan = request.POST.get('id_hewan')
            tgl_pemeriksaan_selanjutnya = request.POST.get('tgl_pemeriksaan_selanjutnya')
            freq_pemeriksaan_rutin = request.POST.get('freq_pemeriksaan_rutin', 3) 
          
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menambah jadwal pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            cursor.execute("""
                SELECT COUNT(*) FROM JADWAL_PEMERIKSAAN_KESEHATAN 
                WHERE id_hewan = %s
            """, (id_hewan,))
            
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                messages.error(request, 'Jadwal pemeriksaan untuk hewan ini sudah ada. Silakan edit jadwal yang sudah ada.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            cursor.execute("SET client_min_messages TO NOTICE;")
            
            cursor.execute("""
                INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN 
                (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                VALUES (%s, %s, %s)
            """, (
                id_hewan,
                tgl_pemeriksaan_selanjutnya,
                int(freq_pemeriksaan_rutin)
            ))
            
            for notice in conn.notices:
                if 'SUKSES:' in notice:
                    messages.success(request, notice.strip())
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil ditambahkan!')
            return redirect('medical_checkup_feeding:medical_checkup')
            
        except Exception as e:
            messages.error(request, f'Error adding checkup schedule: {str(e)}')
            return redirect('medical_checkup_feeding:medical_checkup')
    
    return redirect('medical_checkup_feeding:medical_checkup')
            

@dokter_hewan_required
def edit_checkup_schedule(request, id_hewan, tgl_pemeriksaan_selanjutnya):
    """View untuk mengedit jadwal pemeriksaan kesehatan"""
    if request.method == 'POST':
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
            
            tgl_pemeriksaan_baru = request.POST.get('tgl_pemeriksaan_selanjutnya')
            
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat mengedit jadwal pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            cursor.execute("""
                UPDATE JADWAL_PEMERIKSAAN_KESEHATAN 
                SET tgl_pemeriksaan_selanjutnya = %s
                WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
            """, (
                tgl_pemeriksaan_baru,
                id_hewan,
                tgl_pemeriksaan_selanjutnya
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil diperbarui!')
            return redirect('medical_checkup_feeding:medical_checkup')
            
        except Exception as e:
            messages.error(request, f'Error updating checkup schedule: {str(e)}')
            return redirect('medical_checkup_feeding:medical_checkup')
    
    return redirect('medical_checkup_feeding:medical_checkup')

@dokter_hewan_required
def edit_checkup_frequency(request, id_hewan, tgl_pemeriksaan_selanjutnya):
    """View untuk mengedit frekuensi pemeriksaan rutin"""
    if request.method == 'POST':
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
            freq_pemeriksaan_rutin = request.POST.get('freq_pemeriksaan_rutin')
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat mengedit frekuensi pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            cursor.execute("""
                UPDATE JADWAL_PEMERIKSAAN_KESEHATAN 
                SET freq_pemeriksaan_rutin = %s
                WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
            """, (
                int(freq_pemeriksaan_rutin),
                id_hewan,
                tgl_pemeriksaan_selanjutnya
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Frekuensi pemeriksaan rutin berhasil diperbarui!')
            return redirect('medical_checkup_feeding:medical_checkup')
            
        except Exception as e:
            messages.error(request, f'Error updating checkup frequency: {str(e)}')
            return redirect('medical_checkup_feeding:medical_checkup')
    
    return redirect('medical_checkup_feeding:medical_checkup')

@dokter_hewan_required
def delete_checkup_schedule(request, id_hewan, tgl_pemeriksaan_selanjutnya):
    """View untuk menghapus jadwal pemeriksaan kesehatan"""
    if request.method == 'POST':
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
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.session.get('username'),))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menghapus jadwal pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            
            confirm = request.POST.get('confirm_delete')
            if confirm == 'YA':
                cursor.execute("""
                    DELETE FROM JADWAL_PEMERIKSAAN_KESEHATAN 
                    WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """, (id_hewan, tgl_pemeriksaan_selanjutnya))
                
                conn.commit()
                messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil dihapus!')
            else:
                messages.info(request, 'Penghapusan jadwal dibatalkan.')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            messages.error(request, f'Error deleting checkup schedule: {str(e)}')
    
    return redirect('medical_checkup_feeding:medical_checkup')

@penjaga_hewan_required
def feeding_schedule(request):
    """View untuk menampilkan jadwal pemberian pakan dan riwayat"""
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
            SELECT 
                p.id_hewan,
                p.jadwal,
                p.jenis,
                p.jumlah,
                CASE 
                    WHEN p.status = 'Habis' THEN 'Selesai Diberikan'
                    ELSE 'Menunggu Pemberian'
                END as status,
                h.nama as nama_hewan,
                h.spesies,
                h.asal_hewan,
                h.tanggal_lahir,
                h.nama_habitat,
                h.status_kesehatan
            FROM PAKAN p
            JOIN HEWAN h ON p.id_hewan = h.id
            ORDER BY p.jadwal DESC
            """)
            
        pakan_data = cursor.fetchall()
        cursor.execute("""
            SELECT id, nama, spesies, status_kesehatan, asal_hewan, nama_habitat
            FROM HEWAN
            ORDER BY nama
        """)
        
        hewan_data = cursor.fetchall()
        cursor.execute("""
            SELECT 
                p.id_hewan,
                p.jadwal,
                p.jenis,
                p.jumlah,
                'Selesai Diberikan' as status,
                h.nama as nama_hewan,
                h.spesies,
                h.asal_hewan,
                h.tanggal_lahir,
                h.nama_habitat,
                h.status_kesehatan,
                m.username_jh
            FROM PAKAN p
            JOIN HEWAN h ON p.id_hewan = h.id
            LEFT JOIN MEMBERI m ON p.id_hewan = m.id_hewan
            WHERE p.status = 'Habis' 
            AND EXISTS (
                SELECT 1 FROM MEMBERI m2 
                WHERE m2.id_hewan = p.id_hewan 
                AND m2.username_jh = %s
            )
            ORDER BY p.jadwal DESC
        """, (request.session.get('username'),))
        
        feeding_history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = {
            'pakan_data': pakan_data,
            'hewan_data': hewan_data,
            'feeding_history': feeding_history,
        }
        
        return render(request, 'feeding_schedule.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading feeding data: {str(e)}')
        return render(request, 'feeding_schedule.html', {'pakan_data': [], 'hewan_data': [], 'feeding_history': []})


@penjaga_hewan_required
def add_feeding_schedule(request):
    """View untuk menambah jadwal pemberian pakan baru"""
    if request.method == 'POST':
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
          
            id_hewan = request.POST.get('id_hewan')
            jenis_pakan = request.POST.get('jenis_pakan')
            jumlah_pakan = request.POST.get('jumlah_pakan')
            jadwal = request.POST.get('jadwal')
           
            cursor.execute("""
                INSERT INTO PAKAN 
                (id_hewan, jadwal, jenis, jumlah, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                id_hewan,
                jadwal,
                jenis_pakan,
                int(jumlah_pakan),
                'Tersedia' 
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Jadwal pemberian pakan berhasil ditambahkan!')
            return redirect('medical_checkup_feeding:feeding_schedule')
            
        except Exception as e:
            messages.error(request, f'Error adding feeding schedule: {str(e)}')
            return redirect('medical_checkup_feeding:feeding_schedule')
    
    return redirect('medical_checkup_feeding:feeding_schedule')

@penjaga_hewan_required
def edit_feeding_schedule(request, id_hewan, jadwal):
    """View untuk mengedit jadwal pemberian pakan"""
    if request.method == 'POST':
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
                SELECT status FROM PAKAN 
                WHERE id_hewan = %s AND jadwal = %s
            """, (id_hewan, jadwal))
            
            current_status = cursor.fetchone()
            if not current_status or current_status[0] == 'Habis':
                messages.error(request, 'Jadwal pakan yang sudah selesai diberikan tidak dapat diedit.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:feeding_schedule')
          
            jenis_pakan_baru = request.POST.get('jenis_pakan_baru')
            jumlah_pakan_baru = request.POST.get('jumlah_pakan_baru')
            jadwal_baru = request.POST.get('jadwal_baru')
            
            cursor.execute("""
                UPDATE PAKAN 
                SET jenis = %s, jumlah = %s, jadwal = %s
                WHERE id_hewan = %s AND jadwal = %s AND status != 'Habis'
            """, (
                jenis_pakan_baru,
                int(jumlah_pakan_baru),
                jadwal_baru,
                id_hewan,
                jadwal
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Jadwal pemberian pakan berhasil diperbarui!')
            return redirect('medical_checkup_feeding:feeding_schedule')
            
        except Exception as e:
            messages.error(request, f'Error updating feeding schedule: {str(e)}')
            return redirect('medical_checkup_feeding:feeding_schedule')
    
    return redirect('medical_checkup_feeding:feeding_schedule')

@penjaga_hewan_required
def delete_feeding_schedule(request, id_hewan, jadwal):
    """View untuk menghapus jadwal pemberian pakan"""
    if request.method == 'POST':
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
                SELECT status FROM PAKAN 
                WHERE id_hewan = %s AND jadwal = %s
            """, (id_hewan, jadwal))
            
            current_status = cursor.fetchone()
            if not current_status or current_status[0] == 'Habis':
                messages.error(request, 'Jadwal pakan yang sudah selesai diberikan tidak dapat dihapus.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:feeding_schedule')
         
            confirm = request.POST.get('confirm_delete')
            if confirm == 'YA':
                cursor.execute("""
                    DELETE FROM PAKAN 
                    WHERE id_hewan = %s AND jadwal = %s AND status != 'Habis'
                """, (id_hewan, jadwal))
                
                conn.commit()
                messages.success(request, 'Jadwal pemberian pakan berhasil dihapus!')
            else:
                messages.info(request, 'Penghapusan jadwal dibatalkan.')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            messages.error(request, f'Error deleting feeding schedule: {str(e)}')
    
    return redirect('medical_checkup_feeding:feeding_schedule')

@penjaga_hewan_required
def give_feeding(request, id_hewan, jadwal):
    """View untuk memberikan pakan (ubah status menjadi 'Habis')"""
    if request.method == 'POST':
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
                UPDATE PAKAN 
                SET status = 'Habis'
                WHERE id_hewan = %s AND jadwal = %s AND status != 'Habis'
            """, (id_hewan, jadwal))
            cursor.execute("""
                INSERT INTO MEMBERI (id_hewan, jadwal, username_jh)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_hewan) DO UPDATE SET
                jadwal = EXCLUDED.jadwal,
                username_jh = EXCLUDED.username_jh
            """, (id_hewan, jadwal, request.session.get('username')))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Pakan berhasil diberikan!')
            return redirect('medical_checkup_feeding:feeding_schedule')
            
        except Exception as e:
            messages.error(request, f'Error giving feeding: {str(e)}')
            return redirect('medical_checkup_feeding:feeding_schedule')
    
    return redirect('medical_checkup_feeding:feeding_schedule')