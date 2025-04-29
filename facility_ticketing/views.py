from django.shortcuts import render

# Create your views here.
def manajemen_atraksi(request):
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
    
    return render(request, 'manajemen_atraksi.html', {'atraksi_data': atraksi_data})


def manajemen_wahana(request):
    wahana_data = [
        {
            'nama': 'Safari Jeep',
            'kapasitas': '30',
            'jadwal': '2025-04-24 10:30:00',
            'peraturan': 'Pengunjung diharapkan mengenakan sabuk pengaman sepanjang perjalanan, tidak boleh keluar dari kendaraan selama perjalanan.'
        },
        {
            'nama': 'Panggung Pertunjukan Gajah',
            'kapasitas': '100',
            'jadwal': '2025-04-24 14:00:00',
            'peraturan': 'Pengunjung dilarang mendekat ke panggung selama pertunjukan, menjaga jarak aman dari gajah.'
        },
        {
            'nama': 'Balon Udara Edukasi',
            'kapasitas': '20',
            'jadwal': '2025-04-24 09:00:00',
            'peraturan': 'Anak-anak harus didampingi orang tua.'
        },
        {
            'nama': 'Zona Interaktif Serangga',
            'kapasitas': '40',
            'jadwal': '2025-04-24 13:00:00',
            'peraturan': 'Dilarang menyentuh serangga tanpa izin petugas.'
        },
        {
            'nama': 'Simulator Ekspedisi Kutub',
            'kapasitas': '25',
            'jadwal': '2025-04-24 15:00:00',
            'peraturan': 'Wajib menggunakan peralatan keselamatan yang disediakan.'
        }
    ]
    
    return render(request, 'manajemen_wahana.html', {'wahana_data': wahana_data})

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