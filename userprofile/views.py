from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
import psycopg2, os, dotenv
dotenv.load_dotenv()
from django.conf import settings
from functools import wraps

def session_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('base:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@session_required
def profile_view(request):
    username = request.session.get('username') 
    if request.method == 'POST':
        success = update_profile(username, request.POST)
        if success:
            messages.success(request, 'Profil berhasil diperbarui!')
        else:
            messages.error(request, 'Gagal memperbarui profil. Silakan coba lagi.')
        return redirect('userprofile:profile_view')
    
    # Get user profile data
    profile_data = get_user_profile_data(username)
    if not profile_data:
        messages.error(request, 'Profil tidak ditemukan')
        return redirect('base:home')
    
    return render(request, 'profile.html', profile_data)

@session_required
def change_password_view(request):
    username = request.session.get('username')
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        success, message = change_password(
            request.user.username,
            old_password,
            new_password,
            confirm_password
        )
        
        if success:
            messages.success(request, message)
            return redirect('userprofile:profile_view')
        else:
            messages.error(request, message)
    profile_data = get_user_profile_data(username)
    return render(request, 'profile.html', profile_data)

def get_user_profile_data(username):
    """Get user profile data based on role"""
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
            SELECT username, email, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM PENGGUNA 
            WHERE username = %s
        """, (username,))
        
        user_data = cursor.fetchone()
        if not user_data:
            return None
            
        profile_data = {
            'user': {
                'username': user_data[0],
                'email': user_data[1],
                'first_name': user_data[2],
                'middle_name': user_data[3] or '',
                'last_name': user_data[4],
                'phone': user_data[5]
            }
        }
        
        cursor.execute("""
            SELECT alamat, tgl_lahir 
            FROM PENGUNJUNG 
            WHERE username_P = %s
        """, (username,))
        pengunjung_data = cursor.fetchone()
        
        if pengunjung_data:
            profile_data['user_role'] = 'pengunjung'
            profile_data['user']['address'] = pengunjung_data[0]
            profile_data['user']['dob'] = pengunjung_data[1]
        else:
            cursor.execute("""
                SELECT no_STR 
                FROM DOKTER_HEWAN 
                WHERE username_DH = %s
            """, (username,))
            dokter_data = cursor.fetchone()
            
            if dokter_data:
                profile_data['user_role'] = 'dokter_hewan'
                profile_data['user']['certification_number'] = dokter_data[0]
                cursor.execute("""
                    SELECT nama_spesialisasi 
                    FROM SPESIALISASI 
                    WHERE username_SH = %s
                """, (username,))
                specializations = cursor.fetchall()
                
                if specializations:
                    spec = specializations[0][0]
                    if spec in ['mamalia_besar', 'reptil', 'burung_eksotis', 'primata']:
                        profile_data['user']['specialization'] = spec
                    else:
                        profile_data['user']['specialization'] = 'lainnya'
                        profile_data['user']['other_specialization'] = spec
                else:
                    profile_data['user']['specialization'] = 'mamalia_besar'
            else:
                cursor.execute("""
                    SELECT id_staf FROM PENJAGA_HEWAN WHERE username_jh = %s
                    UNION
                    SELECT id_staf FROM PELATIH_HEWAN WHERE username_lh = %s
                    UNION
                    SELECT id_staf FROM STAF_ADMIN WHERE username_sa = %s
                """, (username, username, username))
                staff_data = cursor.fetchone()
                
                if staff_data:
                    profile_data['user_role'] = 'staff'
                    profile_data['user']['id_staf'] = staff_data[0]
                else:
                    profile_data['user_role'] = 'unknown'
        
        cursor.close()
        conn.close()
        return profile_data
        
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None

def update_profile(username, post_data):
    """Update user profile"""
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
            UPDATE PENGGUNA 
            SET email = %s, nama_depan = %s, nama_tengah = %s, 
                nama_belakang = %s, no_telepon = %s
            WHERE username = %s
        """, (
            post_data.get('email'),
            post_data.get('first_name'),
            post_data.get('middle_name') or None,
            post_data.get('last_name'),
            post_data.get('phone'),
            username
        ))
        
        if post_data.get('address') and post_data.get('dob'):
            cursor.execute("""
                UPDATE PENGUNJUNG 
                SET alamat = %s, tgl_lahir = %s
                WHERE username_P = %s
            """, (
                post_data.get('address'),
                post_data.get('dob'),
                username
            ))
        
        if post_data.get('specialization'):
            specialization = post_data.get('specialization')
            if specialization == 'lainnya':
                specialization = post_data.get('other_specialization', 'lainnya')
          
            cursor.execute("""
                DELETE FROM SPESIALISASI WHERE username_SH = %s
            """, (username,))
           
            cursor.execute("""
                INSERT INTO SPESIALISASI (username_SH, nama_spesialisasi)
                VALUES (%s, %s)
            """, (username, specialization))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False

def change_password(username, old_password, new_password, confirm_password):
    """Change user password"""
    try:
        if new_password != confirm_password:
            return False, "Password baru dan konfirmasi password tidak cocok."
        
        if len(new_password) < 6:
            return False, "Password baru harus minimal 6 karakter."
        
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
            SELECT password FROM PENGGUNA WHERE username = %s
        """, (username,))
        
        stored_password = cursor.fetchone()
        if not stored_password or stored_password[0] != old_password:
            cursor.close()
            conn.close()
            return False, "Password lama tidak benar."
        
     
        cursor.execute("""
            UPDATE PENGGUNA 
            SET password = %s 
            WHERE username = %s
        """, (new_password, username))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Password berhasil diubah!"
        
    except Exception as e:
        print(f"Error changing password: {e}")
        return False, "Terjadi kesalahan saat mengubah password."
