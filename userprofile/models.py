from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Pengguna(AbstractUser):
    email = models.EmailField(unique=True)
    nama_tengah = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=15)
    
    class Meta:
        db_table = 'SIZOPI"."PENGGUNA'
        
    def save(self, *args, **kwargs):
        # Map Django user fields to custom table fields
        self.username = self.username
        self.first_name = self.nama_depan if hasattr(self, 'nama_depan') else self.first_name
        self.last_name = self.nama_belakang if hasattr(self, 'nama_belakang') else self.last_name
        super().save(*args, **kwargs)

class Pengunjung(models.Model):
    username_P = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_P', related_name='pengunjung_profile')
    alamat = models.CharField(max_length=200)
    tgl_lahir = models.DateField()
    
    class Meta:
        db_table = 'SIZOPI"."PENGUNJUNG'

class DokterHewan(models.Model):
    username_DH = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_DH', related_name='dokter_profile')
    no_STR = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'SIZOPI"."DOKTER_HEWAN'

class Spesialisasi(models.Model):
    username_SH = models.ForeignKey(DokterHewan, on_delete=models.CASCADE, db_column='username_SH')
    nama_spesialisasi = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'SIZOPI"."SPESIALISASI'
        unique_together = ('username_SH', 'nama_spesialisasi')

class Staff(models.Model):
    id_staf = models.UUIDField(default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True

class PenjagaHewan(Staff):
    username_jh = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_jh', related_name='penjaga_profile')
    
    class Meta:
        db_table = 'SIZOPI"."PENJAGA_HEWAN'

class PelatihHewan(Staff):
    username_lh = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_lh', related_name='pelatih_profile')
    
    class Meta:
        db_table = 'SIZOPI"."PELATIH_HEWAN'

class StafAdmin(Staff):
    username_sa = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_sa', related_name='admin_profile')
    
    class Meta:
        db_table = 'SIZOPI"."STAF_ADMIN'