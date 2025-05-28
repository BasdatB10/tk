import psycopg2
from django.conf import settings

def user_role_and_status(request):
    """
    Context processor untuk mendapatkan role user dan status adopter
    """
    if 'username' not in request.session:
        return {
            'user_role': None,
            'is_adopter': False,
            'is_authenticated': False
        }

    username = request.session['username']
    print(f"Debug - Context Processor: Username from session: {username}")
    
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
        
        # Cek role user
        role = None
        
        # Cek di setiap tabel staff
        cur.execute("SELECT 1 FROM SIZOPI.dokter_hewan WHERE username_dh = %s", (username,))
        if cur.fetchone():
            role = 'dokter_hewan'
        else:
            cur.execute("SELECT 1 FROM SIZOPI.penjaga_hewan WHERE username_jh = %s", (username,))
            if cur.fetchone():
                role = 'penjaga_hewan'
            else:
                cur.execute("SELECT 1 FROM SIZOPI.pelatih_hewan WHERE username_lh = %s", (username,))
                if cur.fetchone():
                    role = 'pelatih_hewan'
                
                else:
                        cur.execute("SELECT 1 FROM SIZOPI.staf_admin WHERE username_sa = %s", (username,))
                        if cur.fetchone():
                            role = 'staf_admin'
                        else:
                            # Jika tidak ada di tabel staff, berarti pengunjung
                            role = 'pengunjung'
        
        # Cek status adopter
        cur.execute("SELECT 1 FROM SIZOPI.adopter WHERE username_adopter = %s", (username,))
        is_adopter = cur.fetchone() is not None
        
        print(f"Debug - Context Processor: User Role: {role}")
        print(f"Debug - Context Processor: Is Adopter: {is_adopter}")
        
        return {
            'user_role': role,
            'is_adopter': is_adopter,
            'is_authenticated': True
        }
        
    except Exception as e:
        print(f"Debug - Context Processor Error: {str(e)}")
        return {
            'user_role': None,
            'is_adopter': False,
            'is_authenticated': False
        }
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close() 