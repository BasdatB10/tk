SET search_path TO SIZOPI;

CREATE OR REPLACE FUNCTION trigger_sync_medical_checkup()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    next_checkup_date DATE;
    frequency_months INTEGER;
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status_kesehatan = 'Sakit' THEN
        -- Cek apakah sudah ada jadwal pemeriksaan untuk hewan ini
        SELECT freq_pemeriksaan_rutin INTO frequency_months
        FROM JADWAL_PEMERIKSAAN_KESEHATAN 
        WHERE id_hewan = NEW.id_hewan
        LIMIT 1;
        IF frequency_months IS NULL THEN
            frequency_months := 1; -- Default 1 bulan jika tidak ada jadwal
            next_checkup_date := NEW.tanggal_pemeriksaan + INTERVAL '7 days';
        ELSE
            -- Hitung tanggal pemeriksaan selanjutnya berdasarkan frekuensi
            next_checkup_date := NEW.tanggal_pemeriksaan + (frequency_months || ' months')::INTERVAL;
        END IF;
        
        -- Update atau insert jadwal pemeriksaan selanjutnya
        INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
        VALUES (NEW.id_hewan, next_checkup_date, frequency_months)
        ON CONFLICT (id_hewan, tgl_pemeriksaan_selanjutnya) 
        DO UPDATE SET 
            tgl_pemeriksaan_selanjutnya = EXCLUDED.tgl_pemeriksaan_selanjutnya,
            freq_pemeriksaan_rutin = EXCLUDED.freq_pemeriksaan_rutin;
            
        RAISE NOTICE 'SUKSES: Jadwal pemeriksaan hewan "%" telah diperbarui karena status kesehatan "Sakit"', 
                     (SELECT nama FROM HEWAN WHERE id = NEW.id_hewan);
    END IF;
    
    RETURN NEW;
END;
$$;

-- Buat trigger untuk tabel CATATAN_MEDIS
DROP TRIGGER IF EXISTS sync_medical_checkup_trigger ON CATATAN_MEDIS;
CREATE TRIGGER sync_medical_checkup_trigger
    AFTER INSERT OR UPDATE ON CATATAN_MEDIS
    FOR EACH ROW
    EXECUTE FUNCTION trigger_sync_medical_checkup();

-- Function untuk trigger penambahan jadwal otomatis
CREATE OR REPLACE FUNCTION trigger_auto_schedule_checkup()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_checkup_date DATE;
BEGIN
    -- Ketika dibuat jadwal pemeriksaan baru
    IF TG_OP = 'INSERT' THEN
        -- Hitung tanggal pemeriksaan berikutnya berdasarkan frekuensi
        new_checkup_date := NEW.tgl_pemeriksaan_selanjutnya + (NEW.freq_pemeriksaan_rutin || ' months')::INTERVAL;
        
        -- Tambahkan jadwal pemeriksaan rutin berikutnya secara otomatis
        INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
        VALUES (NEW.id_hewan, new_checkup_date, NEW.freq_pemeriksaan_rutin)
        ON CONFLICT (id_hewan, tgl_pemeriksaan_selanjutnya) DO NOTHING;
        
        RAISE NOTICE 'SUKSES: Jadwal pemeriksaan rutin hewan "%" telah ditambahkan sesuai frekuensi.', 
                     (SELECT nama FROM HEWAN WHERE id = NEW.id_hewan);
    END IF;
    
    RETURN NEW;
END;
$$;

-- Buat trigger untuk tabel JADWAL_PEMERIKSAAN_KESEHATAN
DROP TRIGGER IF EXISTS auto_schedule_checkup_trigger ON JADWAL_PEMERIKSAAN_KESEHATAN;
CREATE TRIGGER auto_schedule_checkup_trigger
    AFTER INSERT ON JADWAL_PEMERIKSAAN_KESEHATAN
    FOR EACH ROW
    EXECUTE FUNCTION trigger_auto_schedule_checkup();

-- Function untuk update status kesehatan hewan
CREATE OR REPLACE FUNCTION trigger_update_animal_health()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update status kesehatan hewan berdasarkan rekam medis terbaru
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE HEWAN 
        SET status_kesehatan = NEW.status_kesehatan
        WHERE id = NEW.id_hewan;
        
        RAISE NOTICE 'Status kesehatan hewan "%" telah diperbarui menjadi "%"', 
                     (SELECT nama FROM HEWAN WHERE id = NEW.id_hewan), 
                     NEW.status_kesehatan;
    END IF;
    
    RETURN NEW;
END;
$$;

-- Buat trigger untuk update status kesehatan
DROP TRIGGER IF EXISTS update_animal_health_trigger ON CATATAN_MEDIS;
CREATE TRIGGER update_animal_health_trigger
    AFTER INSERT OR UPDATE ON CATATAN_MEDIS
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_animal_health();
-- Function untuk validasi tanggal pemeriksaan
CREATE OR REPLACE FUNCTION trigger_validate_checkup_date()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Validasi tanggal pemeriksaan tidak boleh di masa lalu (kecuali hari ini)
    IF NEW.tgl_pemeriksaan_selanjutnya < CURRENT_DATE THEN
        RAISE EXCEPTION 'Tanggal pemeriksaan tidak boleh di masa lalu. Tanggal: %', NEW.tgl_pemeriksaan_selanjutnya;
    END IF;
    
    -- Validasi frekuensi pemeriksaan harus positif
    IF NEW.freq_pemeriksaan_rutin <= 0 THEN
        RAISE EXCEPTION 'Frekuensi pemeriksaan harus lebih dari 0 bulan. Frekuensi: %', NEW.freq_pemeriksaan_rutin;
    END IF;
    
    RETURN NEW;
END;
$$;

-- Buat trigger untuk validasi
DROP TRIGGER IF EXISTS validate_checkup_date_trigger ON JADWAL_PEMERIKSAAN_KESEHATAN;
CREATE TRIGGER validate_checkup_date_trigger
    BEFORE INSERT OR UPDATE ON JADWAL_PEMERIKSAAN_KESEHATAN
    FOR EACH ROW
    EXECUTE FUNCTION trigger_validate_checkup_date();
