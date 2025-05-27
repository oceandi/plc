# PLC Simülatör

PLC ödev sorularının Python simülasyonu. Terminal ve GUI destekli.

## Kurulum
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Kullanım
- **Terminal**: `python app.py` → Menüden soru seç
- **GUI**: `python gui_app.py` → Sol panelden soru seç, PLC başlat

## Dosyalar
- `app.py`: Ana simülatör (10 soru çözümü)
- `gui_app.py`: Görsel arayüz (LED, motor, trafik ışığı animasyonları)