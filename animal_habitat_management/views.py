import psycopg2, os, dotenv
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.db import connection
from django.views.decorators.csrf import csrf_protect

dotenv.load_dotenv()

@csrf_protect
def animal(request):
    if 'username' not in request.session:
        return redirect('base:home')
    
    username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM SIZOPI.DOKTER_HEWAN WHERE username_DH = %s
                UNION
                SELECT 1 FROM SIZOPI.PENJAGA_HEWAN WHERE username_jh = %s
                UNION
                SELECT 1 FROM SIZOPI.STAF_ADMIN WHERE username_sa = %s
            );
        """, [username, username, username])
        is_authorized = cursor.fetchone()[0]
    if not is_authorized:
        return redirect('base:dashboard')

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

            id_ = request.POST.get("id")
            nama = request.POST.get("nama")
            spesies = request.POST.get("spesies")
            asal_hewan = request.POST.get("asal_hewan")
            tanggal_lahir = request.POST.get("tanggal_lahir") or None
            status_kesehatan = request.POST.get("status_kesehatan")
            nama_habitat = request.POST.get("nama_habitat") or None
            url_foto = request.POST.get("url_foto")

            if id_:
                conn.notices.clear()
                cursor.execute("""
                    UPDATE SIZOPI.HEWAN
                    SET nama = %s,
                        spesies = %s,
                        asal_hewan = %s,
                        tanggal_lahir = %s,
                        status_kesehatan = %s,
                        nama_habitat = %s,
                        url_foto = %s
                    WHERE id = %s;
                """, (nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto, id_))
                conn.commit()

                notice_message = None
                if conn.notices:
                    for notice in reversed(conn.notices):
                        if 'SUKSES:' in notice:
                            notice_message = notice.strip().replace('NOTICE:', '').replace('SUKSES:', '').strip()
                            break
                message = notice_message or f'Data satwa {nama} berhasil diperbarui.'
            else:
                cursor.execute("""
                    INSERT INTO SIZOPI.HEWAN (
                        id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
                    ) VALUES (
                        gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s
                    );
                """, (nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto))
                conn.commit()
                message = 'Data satwa baru berhasil ditambahkan.'
            return JsonResponse({'success': True, 'message': message})
        except psycopg2.Error as e:
            return JsonResponse({'success': False, 'message': str(e).split("\n")[0].replace("ERROR:", "").strip()}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'message': "Terjadi kesalahan saat menyimpan data hewan."}, status=400)
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM SIZOPI.HEWAN;")
            jumlah_satwa = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM SIZOPI.HEWAN WHERE status_kesehatan = 'Sehat';")
            jumlah_sehat = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM SIZOPI.HEWAN WHERE status_kesehatan = 'Sakit';")
            jumlah_sakit = cursor.fetchone()[0]

            cursor.execute("""
                SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
                FROM SIZOPI.HEWAN;
            """)
            hewan_data = [
                {
                    'id': row[0],
                    'nama': row[1],
                    'spesies': row[2],
                    'asal': row[3],
                    'tanggal_lahir': row[4],
                    'status': row[5],
                    'habitat': row[6],
                    'foto': row[7],
                }
                for row in cursor.fetchall()
            ]

            cursor.execute("SELECT nama FROM SIZOPI.HABITAT;")
            habitat_list = [row[0] for row in cursor.fetchall()]

    return render(request, 'animal.html', {
        'jumlah_satwa': jumlah_satwa,
        'jumlah_sehat': jumlah_sehat,
        'jumlah_sakit': jumlah_sakit,
        'hewan_data': hewan_data,
        'habitat_list': habitat_list
    })

@csrf_protect
def animal_delete(request):
    if request.method == "POST":
        nama = request.POST.get("nama")
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()
            cursor.execute("DELETE FROM SIZOPI.HEWAN WHERE nama = %s;", (nama,))
            conn.commit()
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
        return redirect('animal_habitat_management:animal')

@csrf_protect
def habitat(request):
    if 'username' not in request.session:
        return redirect('base:home')
    
    username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM SIZOPI.DOKTER_HEWAN WHERE username_DH = %s
                UNION
                SELECT 1 FROM SIZOPI.PENJAGA_HEWAN WHERE username_jh = %s
                UNION
                SELECT 1 FROM SIZOPI.STAF_ADMIN WHERE username_sa = %s
            );
        """, [username, username, username])
        is_authorized = cursor.fetchone()[0]
    if not is_authorized:
        return redirect('base:dashboard')

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

            original_nama = request.POST.get("original_nama")
            nama = request.POST.get("nama")
            luas_area = request.POST.get("luas_area")
            kapasitas = request.POST.get("kapasitas")
            status_lingkungan = request.POST.get("status")

            if original_nama:
                cursor.execute("""
                    UPDATE SIZOPI.HABITAT
                    SET nama = %s, luas_area = %s, kapasitas = %s, status = %s
                    WHERE nama = %s;
                """, (nama, luas_area, kapasitas, status_lingkungan, original_nama))
                message = f'Habitat {nama} berhasil diperbarui.'
            else:
                cursor.execute("""
                    INSERT INTO SIZOPI.HABITAT (nama, luas_area, kapasitas, status)
                    VALUES (%s, %s, %s, %s);
                """, (nama, luas_area, kapasitas, status_lingkungan))
                
                message = 'Habitat baru berhasil ditambahkan.'

            conn.commit()
            return JsonResponse({'success': True, 'message': message})
        except psycopg2.Error as e:
            return JsonResponse({'success': False, 'message': str(e).split("\n")[0].replace("ERROR:", "").strip()}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'message': "Terjadi kesalahan saat menambahkan habitat."}, status=400)
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM SIZOPI.HABITAT;")
            jumlah_habitat = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(kapasitas) FROM SIZOPI.HABITAT;")
            kapasitas_total = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT nama, luas_area, kapasitas, status
                FROM SIZOPI.HABITAT;
            """)
            habitat_data = [
                {
                    'nama': row[0],
                    'luas_area': row[1],
                    'kapasitas': row[2],
                    'status': row[3],
                }
                for row in cursor.fetchall()
            ]

        return render(request, 'habitat.html', {
            'jumlah_habitat': jumlah_habitat,
            'kapasitas_total': kapasitas_total,
            'habitat_data': habitat_data
        })
    
@csrf_protect
def habitat_delete(request):
    if request.method == "POST":
        nama = request.POST.get("nama")
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()
            cursor.execute("DELETE FROM SIZOPI.HABITAT WHERE nama = %s;", (nama,))
            conn.commit()
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
        return redirect('animal_habitat_management:habitat')

def habitat_detail(request):
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

            original_nama = request.POST.get('original_nama')
            nama = request.POST.get('nama')
            luas_area = request.POST.get('luas_area')
            kapasitas = request.POST.get('kapasitas')
            status = request.POST.get('status')

            cursor.execute("""
                UPDATE SIZOPI.HABITAT
                SET nama = %s, luas_area = %s, kapasitas = %s, status = %s
                WHERE nama = %s;
            """, [nama, luas_area, kapasitas, status, original_nama])

            conn.commit()
            return JsonResponse({'success': True, 'message': f'Habitat {nama} berhasil diperbarui.'})
        except psycopg2.Error as e:
            return JsonResponse({'success': False, 'message': str(e).split("\n")[0].replace("ERROR:", "").strip()}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'message': "Terjadi kesalahan saat mengubah habitat."}, status=400)
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
        
    else:
        nama = request.GET.get('nama')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nama, luas_area, kapasitas, status
                FROM SIZOPI.HABITAT
                WHERE nama = %s;
            """, [nama])
            habitat_row = cursor.fetchone()
            habitat_data = {
                'nama': habitat_row[0],
                'luas_area': habitat_row[1],
                'kapasitas': habitat_row[2],
                'status': habitat_row[3]
            }

            cursor.execute("""
                SELECT nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan
                FROM SIZOPI.HEWAN
                WHERE nama_habitat = %s;
            """, [nama])
            hewan_list = [
                {
                    'nama': row[0],
                    'spesies': row[1],
                    'asal': row[2],
                    'tanggal_lahir': row[3],
                    'status': row[4]
                }
                for row in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT COUNT(*) FROM SIZOPI.HEWAN WHERE nama_habitat = %s;
            """, [nama])
            jumlah_hewan = cursor.fetchone()[0]

        return render(request, 'habitat_detail.html', {
            'habitat': habitat_data,
            'hewan_list': hewan_list,
            'jumlah_hewan': jumlah_hewan
        })