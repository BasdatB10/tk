from django.shortcuts import render, redirect
import json
import os
from django.conf import settings
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import psycopg2
from django.conf import settings
from datetime import datetime
import uuid

@login_required
def medical_record(request):
    """View untuk menampilkan daftar rekam medis"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Query untuk mendapatkan rekam medis dengan informasi hewan dan dokter
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
        
        # Query untuk mendapatkan daftar hewan
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

@login_required
def add_medical_record(request):
    """View untuk menambah rekam medis baru"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
            status_kesehatan = request.POST.get('status_kesehatan')
            diagnosis = request.POST.get('diagnosis', '')
            pengobatan = request.POST.get('pengobatan', '')
            
            # Validasi: hanya dokter hewan yang bisa menambah rekam medis
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menambah rekam medis.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_record')
            
            # Insert rekam medis baru
            cursor.execute("""
                INSERT INTO CATATAN_MEDIS 
                (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_hewan,
                request.user.username,
                tanggal_pemeriksaan,
                diagnosis if diagnosis else None,
                pengobatan if pengobatan else None,
                status_kesehatan,
                None  # catatan_tindak_lanjut akan diisi nanti jika diperlukan
            ))
            
            # Update status kesehatan hewan
            cursor.execute("""
                UPDATE HEWAN 
                SET status_kesehatan = %s 
                WHERE id = %s
            """, (status_kesehatan, id_hewan))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Rekam medis berhasil ditambahkan!')
            return redirect('medical_checkup_feeding:medical_record')
            
        except Exception as e:
            messages.error(request, f'Error adding medical record: {str(e)}')
            return redirect('medical_checkup_feeding:medical_record')
    
    # GET request - tampilkan form
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil daftar hewan
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

@login_required
def edit_medical_record(request, id_hewan, tanggal_pemeriksaan):
    """View untuk mengedit rekam medis (hanya untuk hewan yang sakit)"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut', '')
            diagnosis_baru = request.POST.get('diagnosis_baru', '')
            pengobatan_baru = request.POST.get('pengobatan_baru', '')
            
            # Update rekam medis
            cursor.execute("""
                UPDATE CATATAN_MEDIS 
                SET catatan_tindak_lanjut = %s,
                    diagnosis = COALESCE(NULLIF(%s, ''), diagnosis),
                    pengobatan = COALESCE(NULLIF(%s, ''), pengobatan)
                WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
            """, (
                catatan_tindak_lanjut if catatan_tindak_lanjut else None,
                diagnosis_baru,
                pengobatan_baru,
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
    
    # GET request - tampilkan form edit
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil data rekam medis yang akan diedit
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
                h.status_kesehatan as status_hewan_saat_ini
            FROM CATATAN_MEDIS cm
            JOIN HEWAN h ON cm.id_hewan = h.id
            WHERE cm.id_hewan = %s AND cm.tanggal_pemeriksaan = %s
        """, (id_hewan, tanggal_pemeriksaan))
        
        medical_record = cursor.fetchone()
        
        if not medical_record:
            messages.error(request, 'Rekam medis tidak ditemukan.')
            cursor.close()
            conn.close()
            return redirect('medical_checkup_feeding:medical_record')
        
        # Cek apakah hewan sakit (hanya bisa edit jika sakit)
        if medical_record[8] != 'Sakit':  # status_hewan_saat_ini
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

@login_required
def delete_medical_record(request, id_hewan, tanggal_pemeriksaan):
    """View untuk menghapus rekam medis"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Validasi: hanya dokter hewan yang bisa menghapus
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menghapus rekam medis.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_record')
            
            # Hapus rekam medis
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


@login_required
def medical_checkup(request):
    """View untuk menampilkan jadwal pemeriksaan kesehatan"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Query untuk mendapatkan jadwal pemeriksaan kesehatan dengan informasi hewan
        cursor.execute("""
            SELECT 
                jpk.id_hewan,
                jpk.tgl_pemeriksaan_selanjutnya,
                jpk.freq_pemeriksaan_rutin,
                h.nama as nama_hewan,
                h.spesies,
                h.status_kesehatan,
                h.nama_habitat
            FROM JADWAL_PEMERIKSAAN_KESEHATAN jpk
            JOIN HEWAN h ON jpk.id_hewan = h.id
            ORDER BY jpk.tgl_pemeriksaan_selanjutnya ASC
        """)
        
        medical_checkup = cursor.fetchall()
        
        # Query untuk mendapatkan daftar hewan yang dipilih dokter hewan
        cursor.execute("""
            SELECT id, nama, spesies, status_kesehatan, nama_habitat
            FROM HEWAN
            ORDER BY nama
        """)
        
        animals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = {
            'medical_checkup': medical_checkup,
            'animals': animals,
        }
        
        return render(request, 'medical_checkup.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading medical checkup schedule: {str(e)}')
        return render(request, 'medical_checkup.html', {'medical_checkup': [], 'animals': []})

@login_required
def add_checkup_schedule(request):
    """View untuk menambah jadwal pemeriksaan kesehatan baru"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            id_hewan = request.POST.get('id_hewan')
            tgl_pemeriksaan_selanjutnya = request.POST.get('tgl_pemeriksaan_selanjutnya')
            freq_pemeriksaan_rutin = request.POST.get('freq_pemeriksaan_rutin', 3)  # default 3 bulan
            
            # Validasi: hanya dokter hewan yang bisa menambah jadwal
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat menambah jadwal pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            # Cek apakah jadwal untuk hewan ini sudah ada
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
            
            # Insert jadwal pemeriksaan baru
            cursor.execute("""
                INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN 
                (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                VALUES (%s, %s, %s)
            """, (
                id_hewan,
                tgl_pemeriksaan_selanjutnya,
                int(freq_pemeriksaan_rutin)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil ditambahkan!')
            return redirect('medical_checkup_feeding:medical_checkup')
            
        except Exception as e:
            messages.error(request, f'Error adding checkup schedule: {str(e)}')
            return redirect('medical_checkup_feeding:medical_checkup')
    
    return redirect('medical_checkup_feeding:medical_checkup')

@login_required
def edit_checkup_schedule(request, id_hewan, tgl_pemeriksaan_selanjutnya):
    """View untuk mengedit jadwal pemeriksaan kesehatan"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            tgl_pemeriksaan_baru = request.POST.get('tgl_pemeriksaan_selanjutnya')
            
            # Validasi: hanya dokter hewan yang bisa mengedit
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat mengedit jadwal pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            # Update jadwal pemeriksaan
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

@login_required
def edit_checkup_frequency(request, id_hewan, tgl_pemeriksaan_selanjutnya):
    """View untuk mengedit frekuensi pemeriksaan rutin"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            freq_pemeriksaan_rutin = request.POST.get('freq_pemeriksaan_rutin')
            
            # Validasi: hanya dokter hewan yang bisa mengedit
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya dokter hewan yang dapat mengedit frekuensi pemeriksaan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:medical_checkup')
            
            # Update frekuensi pemeriksaan
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

@login_required
def delete_checkup_schedule(request, id_hewan, tgl_pemeriksaan_selanjutnya):
    """View untuk menghapus jadwal pemeriksaan kesehatan"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Validasi: hanya dokter hewan yang bisa menghapus
            cursor.execute("""
                SELECT username_DH FROM DOKTER_HEWAN WHERE username_DH = %s
            """, (request.user.username,))
            
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


@login_required
def feeding_schedule(request):
    """View untuk menampilkan jadwal pemberian pakan"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Query untuk mendapatkan jadwal pemberian pakan dengan status "Menunggu Pemberian"
        cursor.execute("""
            SELECT 
                p.id_hewan,
                p.jadwal,
                p.jenis,
                p.jumlah,
                p.status,
                h.nama as nama_hewan,
                h.spesies,
                h.asal_hewan,
                h.tanggal_lahir,
                h.nama_habitat,
                h.status_kesehatan
            FROM PAKAN p
            JOIN HEWAN h ON p.id_hewan = h.id
            WHERE p.status = 'Menunggu Pemberian'
            ORDER BY p.jadwal ASC
        """)
        
        pakan_data = cursor.fetchall()
        
        # Query untuk mendapatkan daftar hewan
        cursor.execute("""
            SELECT id, nama, spesies, status_kesehatan
            FROM HEWAN
            ORDER BY nama
        """)
        
        hewan_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = {
            'pakan_data': pakan_data,
            'hewan_data': hewan_data,
        }
        
        return render(request, 'feeding_schedule.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading feeding schedule: {str(e)}')
        return render(request, 'feeding_schedule.html', {'pakan_data': [], 'hewan_data': []})

@login_required
def add_feeding_schedule(request):
    """View untuk menambah jadwal pemberian pakan baru"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            id_hewan = request.POST.get('id_hewan')
            jenis_pakan = request.POST.get('jenis_pakan')
            jumlah_pakan = request.POST.get('jumlah_pakan')
            jadwal = request.POST.get('jadwal')
            
            # Validasi: hanya penjaga hewan yang bisa menambah jadwal pakan
            cursor.execute("""
                SELECT username_jh FROM PENJAGA_HEWAN WHERE username_jh = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya penjaga hewan yang dapat menambah jadwal pemberian pakan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:feeding_schedule')
            
            # Insert jadwal pakan baru
            cursor.execute("""
                INSERT INTO PAKAN 
                (id_hewan, jadwal, jenis, jumlah, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                id_hewan,
                jadwal,
                jenis_pakan,
                int(jumlah_pakan),
                'Menunggu Pemberian'
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

@login_required
def edit_feeding_schedule(request, id_hewan, jadwal):
    """View untuk mengedit jadwal pemberian pakan"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data dari form
            jenis_pakan_baru = request.POST.get('jenis_pakan_baru')
            jumlah_pakan_baru = request.POST.get('jumlah_pakan_baru')
            jadwal_baru = request.POST.get('jadwal_baru')
            
            # Validasi: hanya penjaga hewan yang bisa mengedit
            cursor.execute("""
                SELECT username_jh FROM PENJAGA_HEWAN WHERE username_jh = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya penjaga hewan yang dapat mengedit jadwal pemberian pakan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:feeding_schedule')
            
            # Update jadwal pakan
            cursor.execute("""
                UPDATE PAKAN 
                SET jenis = %s, jumlah = %s, jadwal = %s
                WHERE id_hewan = %s AND jadwal = %s AND status = 'Menunggu Pemberian'
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

@login_required
def delete_feeding_schedule(request, id_hewan, jadwal):
    """View untuk menghapus jadwal pemberian pakan"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Validasi: hanya penjaga hewan yang bisa menghapus
            cursor.execute("""
                SELECT username_jh FROM PENJAGA_HEWAN WHERE username_jh = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya penjaga hewan yang dapat menghapus jadwal pemberian pakan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:feeding_schedule')
            
            # Konfirmasi penghapusan
            confirm = request.POST.get('confirm_delete')
            if confirm == 'YA':
                # Hapus jadwal pakan
                cursor.execute("""
                    DELETE FROM PAKAN 
                    WHERE id_hewan = %s AND jadwal = %s AND status = 'Menunggu Pemberian'
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

@login_required
def give_feeding(request, id_hewan, jadwal):
    """View untuk memberikan pakan (ubah status menjadi 'Selesai Diberikan')"""
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
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Validasi: hanya penjaga hewan yang bisa memberikan pakan
            cursor.execute("""
                SELECT username_jh FROM PENJAGA_HEWAN WHERE username_jh = %s
            """, (request.user.username,))
            
            if not cursor.fetchone():
                messages.error(request, 'Hanya penjaga hewan yang dapat memberikan pakan.')
                cursor.close()
                conn.close()
                return redirect('medical_checkup_feeding:feeding_schedule')
            
            # Update status pakan menjadi 'Selesai Diberikan'
            cursor.execute("""
                UPDATE PAKAN 
                SET status = 'Selesai Diberikan'
                WHERE id_hewan = %s AND jadwal = %s AND status = 'Menunggu Pemberian'
            """, (id_hewan, jadwal))
            
            # Insert ke tabel MEMBERI untuk mencatat siapa yang memberikan pakan
            cursor.execute("""
                INSERT INTO MEMBERI (id_hewan, jadwal, username_jh)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_hewan) DO UPDATE SET
                jadwal = EXCLUDED.jadwal,
                username_jh = EXCLUDED.username_jh
            """, (id_hewan, jadwal, request.user.username))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messages.success(request, 'Pakan berhasil diberikan!')
            return redirect('medical_checkup_feeding:feeding_schedule')
            
        except Exception as e:
            messages.error(request, f'Error giving feeding: {str(e)}')
            return redirect('medical_checkup_feeding:feeding_schedule')
    
    return redirect('medical_checkup_feeding:feeding_schedule')

@login_required
def feeding_history(request):
    """View untuk menampilkan riwayat pemberian pakan"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Query untuk mendapatkan riwayat pemberian pakan
        cursor.execute("""
            SELECT 
                p.id_hewan,
                p.jadwal,
                p.jenis,
                p.jumlah,
                p.status,
                h.nama as nama_hewan,
                h.spesies,
                h.asal_hewan,
                h.tanggal_lahir,
                h.nama_habitat,
                h.status_kesehatan,
                pg.nama_depan || ' ' || pg.nama_belakang as nama_penjaga
            FROM PAKAN p
            JOIN HEWAN h ON p.id_hewan = h.id
            LEFT JOIN MEMBERI m ON p.id_hewan = m.id_hewan AND p.jadwal = m.jadwal
            LEFT JOIN PENJAGA_HEWAN pj ON m.username_jh = pj.username_jh
            LEFT JOIN PENGGUNA pg ON pj.username_jh = pg.username
            ORDER BY p.jadwal DESC
        """)
        
        feeding_history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        context = {
            'feeding_history': feeding_history
        }
        
        return render(request, 'feeding_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading feeding history: {str(e)}')
        return render(request, 'feeding_history.html', {'feeding_history': []})
