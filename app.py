import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk

class Timer:
    """PLC Timer (TON - Timer On Delay) implementasyonu"""
    def __init__(self, preset_time):
        self.preset_time = preset_time
        self.elapsed_time = 0
        self.done = False
        self.timing = False
        self.start_time = None
    
    def update(self, enable):
        if enable and not self.timing:
            self.start_time = time.time()
            self.timing = True
        elif not enable:
            self.timing = False
            self.elapsed_time = 0
            self.done = False
        
        if self.timing:
            self.elapsed_time = time.time() - self.start_time
            if self.elapsed_time >= self.preset_time:
                self.done = True

class Counter:
    """PLC Counter (CTU - Count Up) implementasyonu"""
    def __init__(self, preset_value):
        self.preset_value = preset_value
        self.current_value = 0
        self.done = False
        self.last_input = False
    
    def count_up(self, input_signal, reset=False):
        """Rising edge detection ve sayma"""
        if reset:
            self.current_value = 0
            self.done = False
            return
        
        # Rising edge detection
        if input_signal and not self.last_input:
            self.current_value += 1
            if self.current_value >= self.preset_value:
                self.done = True
        
        self.last_input = input_signal

class PLCSimulator:
    """Temel PLC Simülatör sınıfı"""
    def __init__(self):
        self.inputs = {}
        self.outputs = {}
        self.timers = {}
        self.counters = {}
        self.internal_relays = {}
        self.running = False
        self.scan_time = 0.01  # 10ms
        
    def scan_cycle(self):
        """PLC scan cycle - sürekli çalışır"""
        while self.running:
            self.execute_logic()
            time.sleep(self.scan_time)
    
    def execute_logic(self):
        """Override edilecek - her uygulama için özel logic"""
        pass
    
    def start(self):
        self.running = True
        self.scan_thread = threading.Thread(target=self.scan_cycle)
        self.scan_thread.daemon = True
        self.scan_thread.start()
    
    def stop(self):
        self.running = False

# SORU 1: Start'a basıldığında motor hemen çalışacak, 15 sn sonra duracak
class Question1_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False}
        self.outputs = {'MOTOR': False}
        self.timers['T1'] = Timer(15.0)
        
    def execute_logic(self):
        # Start butonu ile motor başlatma (rising edge)
        if self.inputs['START'] and not self.outputs['MOTOR']:
            self.outputs['MOTOR'] = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor ÇALIŞTI")
        
        # Timer kontrolü
        self.timers['T1'].update(self.outputs['MOTOR'])
        
        # Timer bittiğinde motor durdurma
        if self.timers['T1'].done:
            self.outputs['MOTOR'] = False
            self.timers['T1'] = Timer(15.0)  # Reset
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor DURDU (15 sn sonra)")

# SORU 2: Motor çalışacak, 10 sn sonra duracak, 10 sn bekleyip tekrar çalışacak
class Question2_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False}
        self.outputs = {'MOTOR': False}
        self.timers = {
            'T_RUN': Timer(10.0),   # Çalışma süresi
            'T_WAIT': Timer(10.0)   # Bekleme süresi
        }
        self.state = 0
        
    def execute_logic(self):
        if self.inputs['START'] and self.state == 0:
            self.state = 1
            self.outputs['MOTOR'] = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor ÇALIŞTI")
        
        if self.state == 1:  # Motor çalışıyor
            self.timers['T_RUN'].update(True)
            if self.timers['T_RUN'].done:
                self.outputs['MOTOR'] = False
                self.state = 2
                self.timers['T_RUN'] = Timer(10.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor DURDU")
        
        elif self.state == 2:  # Bekleme
            self.timers['T_WAIT'].update(True)
            if self.timers['T_WAIT'].done:
                self.outputs['MOTOR'] = True
                self.state = 1
                self.timers['T_WAIT'] = Timer(10.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor TEKRAR ÇALIŞTI")

# SORU 3: Döngüsel çalışma - 15sn bekle, 15sn çalış, 15sn bekle, tekrar çalış
class Question3_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False}
        self.outputs = {'MOTOR': False}
        self.timers = {'T1': Timer(15.0)}
        self.state = 0
        
    def execute_logic(self):
        # Start ile başlatma
        if self.inputs['START'] and self.state == 0:
            self.state = 1
            print("Sistem başladı - 15 sn bekleniyor")
        
        # Stop ile durdurma
        if self.inputs['STOP']:
            self.state = 0
            self.outputs['MOTOR'] = False
            self.timers['T1'] = Timer(15.0)
            print("Sistem durduruldu")
            return
        
        # State machine
        if self.state == 1:  # İlk bekleme
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR'] = True
                self.state = 2
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor ÇALIŞTI")
        
        elif self.state == 2:  # Motor çalışıyor
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR'] = False
                self.state = 3
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor DURDU")
        
        elif self.state == 3:  # Bekleme
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR'] = True
                self.state = 2
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor TEKRAR ÇALIŞTI")

# SORU 4: İki motor sıralı çalışma
class Question4_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False}
        self.outputs = {'MOTOR1': False, 'MOTOR2': False}
        self.timers = {'T1': Timer(15.0)}
        self.state = 0
        
    def execute_logic(self):
        if self.inputs['START'] and self.state == 0:
            self.state = 1
            print("Sistem başladı")
        
        if self.inputs['STOP']:
            self.state = 0
            self.outputs['MOTOR1'] = False
            self.outputs['MOTOR2'] = False
            self.timers['T1'] = Timer(15.0)
            print("Sistem durduruldu")
            return
        
        # State machine - sıralı işlemler
        if self.state == 1:  # 15 sn bekle
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR1'] = True
                self.state = 2
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 1 ÇALIŞTI")
        
        elif self.state == 2:  # Motor1 çalışıyor, 15 sn bekle
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR2'] = True
                self.state = 3
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 2 ÇALIŞTI")
        
        elif self.state == 3:  # Her iki motor çalışıyor, 15 sn bekle
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR1'] = False
                self.state = 4
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 1 DURDU")
        
        elif self.state == 4:  # Sadece Motor2 çalışıyor, 15 sn bekle
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR2'] = False
                self.state = 5
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 2 DURDU")
        
        elif self.state == 5:  # Hiçbir motor çalışmıyor, 15 sn bekle
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['MOTOR1'] = True
                self.state = 2
                self.timers['T1'] = Timer(15.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 1 TEKRAR ÇALIŞTI")

# SORU 5: İki motor - start ile başla, elimizi çekince 1. dur, stop ile 2. dur
class Question5_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False}
        self.outputs = {'MOTOR1': False, 'MOTOR2': False}
        
    def execute_logic(self):
        # Start basılı iken her iki motor çalışır
        if self.inputs['START']:
            self.outputs['MOTOR1'] = True
            self.outputs['MOTOR2'] = True
            if not hasattr(self, 'motors_started'):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 1 ve 2 ÇALIŞTI")
                self.motors_started = True
        else:
            # Start bırakılınca motor1 durur
            if self.outputs['MOTOR1']:
                self.outputs['MOTOR1'] = False
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 1 DURDU")
                self.motors_started = False
        
        # Stop ile motor2 durur
        if self.inputs['STOP']:
            if self.outputs['MOTOR2']:
                self.outputs['MOTOR2'] = False
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 2 DURDU")

# SORU 7: Sensör ve counter ile motor kontrolü
class Question7_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {
            'START': False, 
            'STOP': False, 
            'SENSOR1': False, 
            'SENSOR2': False, 
            'SENSOR3': False
        }
        self.outputs = {
            'MOTOR1': False, 
            'MOTOR2': False, 
            'MOTOR3': False, 
            'MOTOR4': False,
            'LAMP': False
        }
        
    def execute_logic(self):
        # Sensör 1 aktif iken start → Motor 1
        if self.inputs['SENSOR1'] and self.inputs['START']:
            self.outputs['MOTOR1'] = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 1 ÇALIŞTI (Sensör 1)")
        
        # Sensör 2 aktif iken start → Motor 3
        if self.inputs['SENSOR2'] and self.inputs['START']:
            self.outputs['MOTOR3'] = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 3 ÇALIŞTI (Sensör 2)")
        
        # 3 motor çalışıyorken start → Motor 4
        motor_count = sum([self.outputs['MOTOR1'], self.outputs['MOTOR2'], self.outputs['MOTOR3']])
        if motor_count == 3 and self.inputs['START']:
            self.outputs['MOTOR4'] = True
            self.outputs['LAMP'] = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor 4 ÇALIŞTI ve LAMBA YANDI")
        
        # Stop butonu
        if self.inputs['STOP']:
            # Tüm motorları durdur
            for motor in ['MOTOR1', 'MOTOR2', 'MOTOR3', 'MOTOR4']:
                if self.outputs[motor]:
                    self.outputs[motor] = False
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {motor} DURDU")
            
            # Lamba ancak tüm motorlar durduğunda söner
            if not any([self.outputs[f'MOTOR{i}'] for i in range(1, 5)]):
                self.outputs['LAMP'] = False
                print(f"[{datetime.now().strftime('%H:%M:%S')}] LAMBA SÖNDÜ")

# SORU 8: Taşıma bandı - sensör ile ürün sayma
class Question8_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False, 'SENSOR': False}
        self.outputs = {'MOTOR1': False, 'MOTOR2': False, 'MOTOR3': False, 'MOTOR4': False}
        self.counters = {'PRODUCT': Counter(20)}
        self.timers = {
            'T_MOTOR2': Timer(5.0),
            'T_MOTOR3': Timer(5.0),
            'T_MOTOR4': Timer(5.0)
        }
        
    def execute_logic(self):
        # Start ile motor 1 başlar
        if self.inputs['START'] and not self.outputs['MOTOR1']:
            self.outputs['MOTOR1'] = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Taşıma bandı BAŞLADI")
        
        # Stop ile durdur
        if self.inputs['STOP']:
            for i in range(1, 5):
                self.outputs[f'MOTOR{i}'] = False
            self.counters['PRODUCT'] = Counter(20)
            print("Sistem durduruldu")
            return
        
        # Ürün sayma
        if self.outputs['MOTOR1']:
            self.counters['PRODUCT'].count_up(self.inputs['SENSOR'])
            
            count = self.counters['PRODUCT'].current_value
            
            # 5 ürün → Motor 2
            if count >= 5 and not self.outputs['MOTOR2']:
                self.outputs['MOTOR2'] = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 5 ürün - Motor 2 ÇALIŞTI")
            
            # 10 ürün → Motor 3
            if count >= 10 and not self.outputs['MOTOR3']:
                self.outputs['MOTOR3'] = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 10 ürün - Motor 3 ÇALIŞTI")
            
            # 15 ürün → Motor 4
            if count >= 15 and not self.outputs['MOTOR4']:
                self.outputs['MOTOR4'] = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 15 ürün - Motor 4 ÇALIŞTI")
            
            # 20 ürün → Tümünü durdur
            if count >= 20:
                self.outputs['MOTOR1'] = False
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 20 ürün - Sistem DURDU ve SIFIRLANDI")
                self.counters['PRODUCT'] = Counter(20)
        
        # Motor 2, 3, 4 için 5 saniyelik timer
        for i, timer_name in [(2, 'T_MOTOR2'), (3, 'T_MOTOR3'), (4, 'T_MOTOR4')]:
            self.timers[timer_name].update(self.outputs[f'MOTOR{i}'])
            if self.timers[timer_name].done:
                self.outputs[f'MOTOR{i}'] = False
                self.timers[timer_name] = Timer(5.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Motor {i} DURDU (5 sn sonra)")

# SORU 10: Araba yıkama sistemi
class Question10_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {
            'CAR_DETECTED': False,
            'BRUSH_AT_END': False,
            'BRUSH_AT_START': False
        }
        self.outputs = {
            'WATER': False,
            'DETERGENT': False,
            'BRUSH_FORWARD': False,
            'BRUSH_REVERSE': False,
            'HOT_STEAM': False,
            'DRYER': False
        }
        self.timers = {
            'T1': Timer(10.0),  # Su başlatma gecikmesi
            'T2': Timer(20.0),  # Su süresi
            'T3': Timer(5.0),   # Deterjan süresi
            'T4': Timer(10.0),  # Buhar süresi
            'T5': Timer(20.0)   # Kurutma süresi
        }
        self.state = 0
        
    def execute_logic(self):
        # State 0: Bekleme
        if self.state == 0 and self.inputs['CAR_DETECTED']:
            self.state = 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Araba algılandı")
        
        # State 1: 10 sn bekle
        elif self.state == 1:
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.outputs['WATER'] = True
                self.state = 2
                self.timers['T1'] = Timer(10.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Su fışkırtma BAŞLADI")
        
        # State 2: Su + 20 sn sonra deterjan
        elif self.state == 2:
            self.timers['T2'].update(True)
            if self.timers['T2'].done:
                self.outputs['DETERGENT'] = True
                self.state = 3
                self.timers['T2'] = Timer(20.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Deterjan BAŞLADI")
        
        # State 3: Deterjan 5 sn
        elif self.state == 3:
            self.timers['T3'].update(True)
            if self.timers['T3'].done:
                self.outputs['DETERGENT'] = False
                self.outputs['BRUSH_FORWARD'] = True
                self.state = 4
                self.timers['T3'] = Timer(5.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fırçalar İLERİ")
        
        # State 4: Fırçalar ileri - sonuna kadar
        elif self.state == 4:
            if self.inputs['BRUSH_AT_END']:
                self.outputs['BRUSH_FORWARD'] = False
                self.outputs['BRUSH_REVERSE'] = True
                self.state = 5
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fırçalar GERİ")
        
        # State 5: Fırçalar geri - başa dönüş
        elif self.state == 5:
            if self.inputs['BRUSH_AT_START']:
                self.outputs['BRUSH_REVERSE'] = False
                self.outputs['WATER'] = False
                self.outputs['HOT_STEAM'] = True
                self.state = 6
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sıcak buhar BAŞLADI")
        
        # State 6: Buhar 10 sn
        elif self.state == 6:
            self.timers['T4'].update(True)
            if self.timers['T4'].done:
                self.outputs['HOT_STEAM'] = False
                self.outputs['DRYER'] = True
                self.state = 7
                self.timers['T4'] = Timer(10.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Kurutma BAŞLADI")
        
        # State 7: Kurutma 20 sn
        elif self.state == 7:
            self.timers['T5'].update(True)
            if self.timers['T5'].done:
                self.outputs['DRYER'] = False
                self.state = 0
                # Reset timers
                for timer in self.timers.values():
                    timer.done = False
                    timer.timing = False
                self.timers['T5'] = Timer(20.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Yıkama TAMAMLANDI")

# SORU 11: Trafik ışığı
class Question11_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.outputs = {
            'KIRMIZI_ARAC': True,
            'SARI_ARAC': False,
            'YESIL_ARAC': False,
            'KIRMIZI_YAYA': False,
            'YESIL_YAYA': True
        }
        self.timers = {
            'T1': Timer(10.0),
            'T2': Timer(3.0),
            'T3': Timer(10.0),
            'T_BLINK': Timer(0.5),  # Yanıp sönme için
            'T4': Timer(2.0)
        }
        self.state = 1
        self.blink_count = 0
        
    def execute_logic(self):
        # State 1: Araç kırmızı, yaya yeşil (10 sn)
        if self.state == 1:
            self.outputs['KIRMIZI_ARAC'] = True
            self.outputs['SARI_ARAC'] = False
            self.outputs['YESIL_ARAC'] = False
            self.outputs['KIRMIZI_YAYA'] = False
            self.outputs['YESIL_YAYA'] = True
            
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                self.state = 2
                self.timers['T1'] = Timer(10.0)
                print("Sarı ışık yanıyor")
        
        # State 2: Araç sarı, yaya kırmızı (3 sn)
        elif self.state == 2:
            self.outputs['KIRMIZI_ARAC'] = False
            self.outputs['SARI_ARAC'] = True
            self.outputs['YESIL_ARAC'] = False
            self.outputs['KIRMIZI_YAYA'] = True
            self.outputs['YESIL_YAYA'] = False
            
            self.timers['T2'].update(True)
            if self.timers['T2'].done:
                self.state = 3
                self.timers['T2'] = Timer(3.0)
                print("Yeşil ışık yanıyor")
        
        # State 3: Araç yeşil, yaya kırmızı (10 sn)
        elif self.state == 3:
            self.outputs['KIRMIZI_ARAC'] = False
            self.outputs['SARI_ARAC'] = False
            self.outputs['YESIL_ARAC'] = True
            self.outputs['KIRMIZI_YAYA'] = True
            self.outputs['YESIL_YAYA'] = False
            
            self.timers['T3'].update(True)
            if self.timers['T3'].done:
                self.state = 4
                self.timers['T3'] = Timer(10.0)
                self.blink_count = 0
                print("Yeşil ışık yanıp sönüyor")
        
        # State 4: Yeşil yanıp sönme (5 kez)
        elif self.state == 4:
            self.timers['T_BLINK'].update(True)
            if self.timers['T_BLINK'].done:
                self.outputs['YESIL_ARAC'] = not self.outputs['YESIL_ARAC']
                self.blink_count += 1
                self.timers['T_BLINK'] = Timer(0.5)
                
                if self.blink_count >= 10:  # 5 kez yanıp sönme = 10 değişim
                    self.outputs['YESIL_ARAC'] = False
                    self.outputs['SARI_ARAC'] = True
                    self.state = 5
                    print("Sarı ışık (son)")
        
        # State 5: Araç sarı (2 sn)
        elif self.state == 5:
            self.timers['T4'].update(True)
            if self.timers['T4'].done:
                self.state = 1
                self.timers['T4'] = Timer(2.0)
                print("Döngü başa döndü")

# SORU 13: 6 LED'li yürüyen ışık
class Question13_PLC(PLCSimulator):
    def __init__(self):
        super().__init__()
        self.inputs = {'START': False, 'STOP': False}
        self.outputs = {f'LED{i}': False for i in range(1, 7)}
        self.timers = {'T1': Timer(1.0)}
        self.current_led = 0
        self.running = False
        
    def execute_logic(self):
        if self.inputs['START'] and not self.running:
            self.running = True
            self.current_led = 1
            print("Yürüyen ışık başladı")
        
        if self.inputs['STOP']:
            self.running = False
            for i in range(1, 7):
                self.outputs[f'LED{i}'] = False
            print("Yürüyen ışık durdu")
            return
        
        if self.running:
            self.timers['T1'].update(True)
            if self.timers['T1'].done:
                # Tüm LED'leri söndür
                for i in range(1, 7):
                    self.outputs[f'LED{i}'] = False
                
                # Sıradaki LED'i yak
                self.outputs[f'LED{self.current_led}'] = True
                print(f"LED {self.current_led} YANDI")
                
                # Sonraki LED'e geç
                self.current_led = (self.current_led % 6) + 1
                self.timers['T1'] = Timer(1.0)

# GUI için basit bir arayüz
class PLCSimulatorGUI:
    def __init__(self, plc, title="PLC Simülatör"):
        self.plc = plc
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x600")
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık
        ttk.Label(main_frame, text=title, font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Input bölümü
        ttk.Label(main_frame, text="INPUTS", font=('Arial', 12, 'bold')).grid(row=1, column=0, columnspan=2, pady=5)
        
        self.input_vars = {}
        row = 2
        for input_name in self.plc.inputs:
            var = tk.BooleanVar()
            self.input_vars[input_name] = var
            ttk.Checkbutton(main_frame, text=input_name, variable=var,
                          command=lambda n=input_name: self.update_input(n)).grid(row=row, column=0, sticky=tk.W)
            row += 1
        
        # Output bölümü
        ttk.Label(main_frame, text="OUTPUTS", font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        self.output_labels = {}
        for output_name in self.plc.outputs:
            label = ttk.Label(main_frame, text=f"{output_name}: ○", foreground="gray")
            label.grid(row=row, column=0, sticky=tk.W)
            self.output_labels[output_name] = label
            row += 1
        
        # Kontrol butonları
        ttk.Button(main_frame, text="PLC Başlat", command=self.start_plc).grid(row=row, column=0, pady=10)
        ttk.Button(main_frame, text="PLC Durdur", command=self.stop_plc).grid(row=row, column=1, pady=10)
        
        # Güncelleme döngüsü
        self.update_display()
        
    def update_input(self, input_name):
        self.plc.inputs[input_name] = self.input_vars[input_name].get()
    
    def update_display(self):
        # Output durumlarını güncelle
        for output_name, label in self.output_labels.items():
            if self.plc.outputs[output_name]:
                label.config(text=f"{output_name}: ●", foreground="green")
            else:
                label.config(text=f"{output_name}: ○", foreground="gray")
        
        # 100ms sonra tekrar güncelle
        self.root.after(100, self.update_display)
    
    def start_plc(self):
        self.plc.start()
        print("PLC başlatıldı")
    
    def stop_plc(self):
        self.plc.stop()
        print("PLC durduruldu")
    
    def run(self):
        self.root.mainloop()

# Ana menü
def main_menu():
    print("\n" + "="*50)
    print("PLC SİMÜLATÖR - TÜM SORULAR")
    print("="*50)
    print("1.  Motor 15sn çalışıp durma")
    print("2.  Motor 10sn çalış, 10sn dur, tekrar")
    print("3.  15sn bekle, çalış, dur döngüsü")
    print("4.  İki motor sıralı çalışma")
    print("5.  Start basılı motor kontrolü")
    print("7.  Sensör ve 4 motor kontrolü")
    print("8.  Taşıma bandı - ürün sayma")
    print("10. Araba yıkama sistemi")
    print("11. Trafik ışığı")
    print("13. 6 LED yürüyen ışık")
    print("G.  GUI ile test")
    print("Q.  Çıkış")
    print("="*50)
    
    choice = input("Seçiminiz: ").upper()
    
    if choice == '1':
        print("\n--- SORU 1 TEST ---")
        plc = Question1_PLC()
        test_with_timer(plc, 20)
        
    elif choice == '2':
        print("\n--- SORU 2 TEST ---")
        plc = Question2_PLC()
        test_with_timer(plc, 30)
        
    elif choice == '3':
        print("\n--- SORU 3 TEST ---")
        plc = Question3_PLC()
        test_with_timer(plc, 60)
        
    elif choice == '4':
        print("\n--- SORU 4 TEST ---")
        plc = Question4_PLC()
        test_with_timer(plc, 90)
        
    elif choice == '5':
        print("\n--- SORU 5 TEST ---")
        plc = Question5_PLC()
        test_question5(plc)
        
    elif choice == '7':
        print("\n--- SORU 7 TEST ---")
        plc = Question7_PLC()
        test_question7(plc)
        
    elif choice == '8':
        print("\n--- SORU 8 TEST ---")
        plc = Question8_PLC()
        test_question8(plc)
        
    elif choice == '10':
        print("\n--- SORU 10 TEST ---")
        plc = Question10_PLC()
        test_question10(plc)
        
    elif choice == '11':
        print("\n--- SORU 11 TEST ---")
        plc = Question11_PLC()
        test_with_timer(plc, 30, auto_start=False)
        
    elif choice == '13':
        print("\n--- SORU 13 TEST ---")
        plc = Question13_PLC()
        test_with_timer(plc, 15)
        
    elif choice == 'G':
        gui_menu()
        
    elif choice == 'Q':
        print("Çıkış yapılıyor...")
        return False
    
    return True

def gui_menu():
    print("\nGUI için soru seçin:")
    print("1. Soru 1 - Basit motor")
    print("4. Soru 4 - İki motor")
    print("8. Soru 8 - Taşıma bandı")
    print("13. Soru 13 - Yürüyen ışık")
    
    choice = input("Seçim: ")
    
    if choice == '1':
        plc = Question1_PLC()
        gui = PLCSimulatorGUI(plc, "Soru 1 - Motor Kontrolü")
        gui.run()
    elif choice == '4':
        plc = Question4_PLC()
        gui = PLCSimulatorGUI(plc, "Soru 4 - İki Motor")
        gui.run()
    elif choice == '8':
        plc = Question8_PLC()
        gui = PLCSimulatorGUI(plc, "Soru 8 - Taşıma Bandı")
        gui.run()
    elif choice == '13':
        plc = Question13_PLC()
        gui = PLCSimulatorGUI(plc, "Soru 13 - Yürüyen Işık")
        gui.run()

# Test fonksiyonları
def test_with_timer(plc, duration, auto_start=True):
    plc.start()
    
    if auto_start:
        plc.inputs['START'] = True
        time.sleep(0.1)
        plc.inputs['START'] = False
    
    print(f"\n{duration} saniye test ediliyor...")
    print("(CTRL+C ile durdurabilirsiniz)\n")
    
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\nTest durduruldu")
    
    plc.stop()

def test_question5(plc):
    plc.start()
    
    print("\nStart butonuna basılıyor (3 saniye)...")
    plc.inputs['START'] = True
    time.sleep(3)
    
    print("Start bırakılıyor...")
    plc.inputs['START'] = False
    time.sleep(2)
    
    print("Stop butonuna basılıyor...")
    plc.inputs['STOP'] = True
    time.sleep(0.5)
    plc.inputs['STOP'] = False
    
    time.sleep(1)
    plc.stop()

def test_question7(plc):
    plc.start()
    
    print("\nSensör 1 aktif, Start basılıyor...")
    plc.inputs['SENSOR1'] = True
    plc.inputs['START'] = True
    time.sleep(0.1)
    plc.inputs['START'] = False
    time.sleep(2)
    
    print("\nSensör 2 aktif, Start basılıyor...")
    plc.inputs['SENSOR1'] = False
    plc.inputs['SENSOR2'] = True
    plc.inputs['START'] = True
    time.sleep(0.1)
    plc.inputs['START'] = False
    time.sleep(2)
    
    print("\nStop basılıyor...")
    plc.inputs['STOP'] = True
    time.sleep(1)
    
    plc.stop()

def test_question8(plc):
    plc.start()
    
    print("\nTaşıma bandı başlatılıyor...")
    plc.inputs['START'] = True
    time.sleep(0.1)
    plc.inputs['START'] = False
    
    print("\nÜrünler geçiyor...")
    for i in range(1, 21):
        time.sleep(0.5)
        plc.inputs['SENSOR'] = True
        time.sleep(0.1)
        plc.inputs['SENSOR'] = False
        print(f"Ürün {i} geçti")
    
    time.sleep(5)
    plc.stop()

def test_question10(plc):
    plc.start()
    
    print("\nAraba algılanıyor...")
    plc.inputs['CAR_DETECTED'] = True
    time.sleep(0.1)
    plc.inputs['CAR_DETECTED'] = False
    
    # Fırça simülasyonu
    def simulate_brush():
        time.sleep(30)  # İlk işlemler
        print("\n[SİMÜLASYON] Fırça araba sonuna ulaştı")
        plc.inputs['BRUSH_AT_END'] = True
        time.sleep(0.5)
        plc.inputs['BRUSH_AT_END'] = False
        
        time.sleep(5)
        print("[SİMÜLASYON] Fırça başa döndü")
        plc.inputs['BRUSH_AT_START'] = True
        time.sleep(0.5)
        plc.inputs['BRUSH_AT_START'] = False
    
    brush_thread = threading.Thread(target=simulate_brush)
    brush_thread.daemon = True
    brush_thread.start()
    
    # 70 saniye bekle (tüm işlem)
    time.sleep(70)
    plc.stop()

if __name__ == "__main__":
    while main_menu():
        pass