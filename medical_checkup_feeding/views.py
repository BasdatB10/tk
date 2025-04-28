from django.shortcuts import render, redirect
import json
import os
from django.conf import settings
from datetime import datetime

def medical_record(request):
    json_file_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'medical_record.json')
    with open(json_file_path, 'r') as file:
        medical_records = json.load(file)
    
    animals = {}
    for record in medical_records:
        if record["id_hewan"] not in animals:
            animals[record["id_hewan"]] = record.get("nama", "Unknown Animal")
    
    context = {
        'medical_records_raw': medical_records,  
        'medical_records': medical_records, 
        'animals': animals,  
    }
    return render(request, 'medical_record.html', context)

def medical_checkup(request):
    medical_checkup_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'medical_checkup.json')
    hewan_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'hewan.json')
    
    with open(medical_checkup_path, 'r') as file:
        medical_checkup = json.load(file)
    
    with open(hewan_path, 'r') as file:
        hewan_data = json.load(file)
   
    animal_names = {}
    for animal in hewan_data:
        animal_names[animal['id']] = animal.get('nama', 'Unknown Animal')
    
    for checkup in medical_checkup:
        checkup['nama_hewan'] = animal_names.get(checkup['id_hewan'], 'Unknown Animal')
    
    context = {
        'medical_checkup': medical_checkup,
        'animal_names': animal_names
    }
    return render(request, 'medical_checkup.html', context)

def feeding_schedule(request):
    memberi_file_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'memberi.json')
    pakan_file_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'pakan.json')
    hewan_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'hewan.json')
    with open(memberi_file_path, 'r') as file:
        memberi_data = json.load(file)
    with open(pakan_file_path, 'r') as file:
        pakan_data = json.load(file)
    with open(hewan_path, 'r') as file:
        hewan_data = json.load(file)

    animal_display_names = {}
    hewan_map = {}
    for animal in hewan_data:
        hewan_map[animal['id']] = animal
        animal_display_names[animal['id']] = animal.get('nama', f"ID: {animal['id'][:8]}...")
    scheduled_pakan = [p for p in pakan_data if p.get('status') == 'Tersedia']
    context = {
        'pakan_data': scheduled_pakan, 
        'hewan_data': hewan_data,      
        'animal_display_names': animal_display_names,
    }
    return render(request, 'feeding_schedule.html', context)

def feeding_history(request):
    memberi_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'memberi.json')
    pakan_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'pakan.json')
    hewan_path = os.path.join(settings.BASE_DIR, 'medical_checkup_feeding', 'fixtures', 'hewan.json')
    with open(memberi_path, 'r') as file:
        memberi_data = json.load(file)
    with open(pakan_path, 'r') as file:
        pakan_data = json.load(file) 
    with open(hewan_path, 'r') as file:
        hewan_data = json.load(file)
    hewan_map = {animal['id']: animal for animal in hewan_data if 'id' in animal}
    feeding_history = []
    for pakan in pakan_data:
        if 'id_hewan' in pakan:
            animal_id = pakan['id_hewan']
            animal_info = hewan_map.get(animal_id, {})
            record = {
                'jadwal': pakan.get('jadwal'),
                'jenis': pakan.get('jenis'),
                'jumlah': pakan.get('jumlah'),
                'status': pakan.get('status'),
                'id_hewan': animal_id,
                'nama_hewan': animal_info.get('nama', 'Unknown Animal'),
                'spesies': animal_info.get('spesies', 'Unknown Species'),
                'asal_hewan': animal_info.get('asal_hewan', 'Unknown'),
                'tanggal_lahir': animal_info.get('tanggal_lahir'),
                'nama_habitat': animal_info.get('nama_habitat', 'Unknown'),
                'status_kesehatan': animal_info.get('status_kesehatan', 'Unknown')
            }
            feeding_history.append(record)
    
    context = {
        'feeding_history': feeding_history
    }
    return render(request, 'feeding_history.html', context)