SET search_path TO SIZOPI;

CREATE OR REPLACE FUNCTION update_health_check_schedule()
RETURNS TRIGGER AS $$
DECLARE
    next_check_date DATE;
    check_frequency INT;
    existing_schedule RECORD;
BEGIN
    -- Cek jika status kesehatan adalah "Sakit"
    IF NEW.status_kesehatan = 'Sakit' THEN
        -- Cari jadwal pemeriksaan yang ada untuk hewan tersebut
        SELECT * INTO existing_schedule 
        FROM JADWAL_PEMERIKSAAN_KESEHATAN
        WHERE id_hewan = NEW.id_hewan
        ORDER BY tgl_pemeriksaan_selanjutnya DESC
        LIMIT 1;
        
        IF FOUND THEN
            -- Jika ditemukan jadwal, perbarui dengan jadwal baru (7 hari dari sekarang)
            next_check_date := CURRENT_DATE + INTERVAL '7 days';
            check_frequency := existing_schedule.freq_pemeriksaan_rutin;
            
            -- Perbarui jadwal atau buat yang baru
            INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (NEW.id_hewan, next_check_date, check_frequency)
            ON CONFLICT (id_hewan, tgl_pemeriksaan_selanjutnya)
            DO UPDATE SET tgl_pemeriksaan_selanjutnya = next_check_date;
            
            -- Log pesan sukses ke tabel sementara untuk debug (opsional)
            -- Bisa diimplementasikan dengan tabel log jika diperlukan
            
            RAISE NOTICE 'SUKSES: Jadwal pemeriksaan hewan "%" telah diperbarui karena status kesehatan "Sakit".', 
                         (SELECT nama FROM HEWAN WHERE id = NEW.id_hewan);
        ELSE
            -- Jika tidak ada jadwal sebelumnya, buat jadwal baru dengan default 7 hari
            next_check_date := CURRENT_DATE + INTERVAL '7 days';
            check_frequency := 30; -- Default frekuensi 30 hari
            
            INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (NEW.id_hewan, next_check_date, check_frequency);
            
            RAISE NOTICE 'SUKSES: Jadwal pemeriksaan hewan "%" telah dibuat karena status kesehatan "Sakit".', 
                         (SELECT nama FROM HEWAN WHERE id = NEW.id_hewan);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger yang akan dijalankan setelah insert atau update pada catatan medis
CREATE OR REPLACE TRIGGER trigger_update_health_check_after_medical_record
AFTER INSERT OR UPDATE ON CATATAN_MEDIS
FOR EACH ROW
EXECUTE FUNCTION update_health_check_schedule();

-- 2. Penambahan Jadwal Pemeriksaan sesuai Frekuensi
-- Stored Procedure untuk menambahkan jadwal pemeriksaan rutin
CREATE OR REPLACE PROCEDURE add_routine_health_check(animal_id UUID)
LANGUAGE plpgsql AS $$
DECLARE
    last_check RECORD;
    next_date DATE;
    frequency INT;
    animal_name VARCHAR(100);
BEGIN
    -- Dapatkan nama hewan
    SELECT nama INTO animal_name
    FROM HEWAN
    WHERE id = animal_id;
    
    -- Dapatkan jadwal terbaru
    SELECT * INTO last_check
    FROM JADWAL_PEMERIKSAAN_KESEHATAN
    WHERE id_hewan = animal_id
    ORDER BY tgl_pemeriksaan_selanjutnya DESC
    LIMIT 1;
    
    IF FOUND THEN
        -- Hitung tanggal pemeriksaan berikutnya berdasarkan frekuensi
        frequency := last_check.freq_pemeriksaan_rutin;
        next_date := last_check.tgl_pemeriksaan_selanjutnya + (frequency * INTERVAL '1 day');
        
        -- Tambahkan jadwal pemeriksaan baru untuk tahun yang sama
        IF EXTRACT(YEAR FROM next_date) = EXTRACT(YEAR FROM CURRENT_DATE) THEN
            INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (animal_id, next_date, frequency);
            
            RAISE NOTICE 'SUKSES: Jadwal pemeriksaan rutin hewan "%" telah ditambahkan sesuai frekuensi.', animal_name;
        END IF;
    ELSE
        RAISE EXCEPTION 'Tidak ada jadwal pemeriksaan sebelumnya untuk hewan dengan ID %', animal_id;
    END IF;
END;
$$;

-- Fungsi untuk menambahkan jadwal pemeriksaan rutin secara otomatis
CREATE OR REPLACE FUNCTION auto_schedule_routine_checks()
RETURNS TRIGGER AS $$
BEGIN
    -- Tambahkan jadwal pemeriksaan rutin baru sesuai frekuensi
    CALL add_routine_health_check(NEW.id_hewan);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger untuk menambahkan jadwal pemeriksaan rutin otomatis saat jadwal ditambahkan
CREATE OR REPLACE TRIGGER trigger_auto_schedule_routine_checks
AFTER INSERT ON JADWAL_PEMERIKSAAN_KESEHATAN
FOR EACH ROW
WHEN (pg_trigger_depth() < 1) -- Mencegah trigger rekursif (hanya memicu sekali)
EXECUTE FUNCTION auto_schedule_routine_checks();

-- Fungsi untuk memanggil semua jadwal pemeriksaan rutin hewan yang sudah ada
CREATE OR REPLACE PROCEDURE schedule_all_routine_checks()
LANGUAGE plpgsql AS $$
DECLARE
    animal_rec RECORD;
BEGIN
    FOR animal_rec IN 
        SELECT DISTINCT id_hewan 
        FROM JADWAL_PEMERIKSAAN_KESEHATAN
    LOOP
        BEGIN
            CALL add_routine_health_check(animal_rec.id_hewan);
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Terjadi kesalahan saat menjadwalkan pemeriksaan untuk hewan dengan ID %: %', 
                animal_rec.id_hewan, SQLERRM;
        END;
    END LOOP;
END;
$$;