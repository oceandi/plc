import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import queue
import sys
from io import StringIO

# app.py'den import
from app import *

class PLCVisualGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PLC Simülatör - Görsel Arayüz")
        self.root.geometry("1200x700")
        
        # Tema ve stiller
        self.setup_styles()
        
        # Ana container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sol panel - Soru seçimi
        self.create_left_panel(main_container)
        
        # Orta panel - Kontroller ve görsel
        self.create_center_panel(main_container)
        
        # Sağ panel - Konsol çıktısı
        self.create_right_panel(main_container)
        
        # Alt panel - Durum çubuğu
        self.create_status_bar()
        
        # PLC instance
        self.plc = None
        self.update_thread = None
        self.console_queue = queue.Queue()
        
        # Konsol yakalama
        self.setup_console_redirect()
        
        # Güncelleme döngüsü
        self.update_gui()
        
    def setup_styles(self):
        """Görsel stiller"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Buton stilleri
        style.configure('Start.TButton', background='#4CAF50')
        style.configure('Stop.TButton', background='#f44336')
        style.configure('Reset.TButton', background='#FF9800')
        
    def create_left_panel(self, parent):
        """Sol panel - Soru listesi"""
        left_frame = ttk.LabelFrame(parent, text="📋 SORULAR", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Soru listesi
        self.question_listbox = tk.Listbox(left_frame, width=40, height=20)
        self.question_listbox.pack(fill="both", expand=True)
        
        questions = [
            ("Soru 1", "Motor 15sn çalışıp durma", Question1_PLC),
            ("Soru 2", "Motor 10sn çalış-dur döngüsü", Question2_PLC),
            ("Soru 3", "15sn bekle-çalış döngüsü", Question3_PLC),
            ("Soru 4", "İki motor sıralı çalışma", Question4_PLC),
            ("Soru 5", "Start basılı motor kontrolü", Question5_PLC),
            ("Soru 7", "Sensör ve 4 motor kontrolü", Question7_PLC),
            ("Soru 8", "Taşıma bandı - ürün sayma", Question8_PLC),
            ("Soru 10", "Araba yıkama sistemi", Question10_PLC),
            ("Soru 11", "Trafik ışığı sistemi", Question11_PLC),
            ("Soru 13", "6 LED yürüyen ışık", Question13_PLC),
        ]
        
        self.plc_classes = {}
        for i, (num, desc, plc_class) in enumerate(questions):
            self.question_listbox.insert(tk.END, f"{num}: {desc}")
            self.plc_classes[i] = plc_class
            
        # Seçim butonu
        ttk.Button(left_frame, text="Seçili Soruyu Yükle", 
                  command=self.load_selected_question).pack(pady=10)
        
        self.question_listbox.bind('<Double-Button-1>', lambda e: self.load_selected_question())
        
    def create_center_panel(self, parent):
        """Orta panel - Kontroller ve görselleştirme"""
        center_frame = ttk.Frame(parent)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # Üst kontrol paneli
        control_frame = ttk.LabelFrame(center_frame, text="⚙️ KONTROLLER", padding=10)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # PLC kontrol butonları
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        self.start_plc_btn = ttk.Button(button_frame, text="▶️ PLC Başlat", 
                                       command=self.start_plc, style='Start.TButton')
        self.start_plc_btn.grid(row=0, column=0, padx=5)
        
        self.stop_plc_btn = ttk.Button(button_frame, text="⏹️ PLC Durdur", 
                                      command=self.stop_plc, style='Stop.TButton', 
                                      state="disabled")
        self.stop_plc_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="🔄 Reset", 
                  command=self.reset_plc, style='Reset.TButton').grid(row=0, column=2, padx=5)
        
        # Görselleştirme alanı
        self.visual_frame = ttk.LabelFrame(center_frame, text="👁️ GÖRSEL SİMÜLASYON", padding=10)
        self.visual_frame.pack(fill="both", expand=True)
        
        # İçerik çerçevesi
        self.content_frame = ttk.Frame(self.visual_frame)
        self.content_frame.pack(fill="both", expand=True)
        
        # Başlangıç mesajı
        welcome_label = ttk.Label(self.content_frame, 
                                 text="Sol taraftan bir soru seçin",
                                 font=('Arial', 16))
        welcome_label.pack(expand=True)
        
    def create_right_panel(self, parent):
        """Sağ panel - Konsol çıktısı"""
        right_frame = ttk.LabelFrame(parent, text="📟 KONSOL ÇIKTISI", padding=10)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # Konsol text widget
        self.console_text = scrolledtext.ScrolledText(right_frame, width=40, height=25,
                                                     bg='black', fg='lime',
                                                     font=('Consolas', 10))
        self.console_text.pack(fill="both", expand=True)
        
        # Konsol kontrolleri
        console_controls = ttk.Frame(right_frame)
        console_controls.pack(fill="x", pady=(5, 0))
        
        ttk.Button(console_controls, text="Temizle", 
                  command=self.clear_console).pack(side="left", padx=5)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(console_controls, text="Otomatik Kaydır", 
                       variable=self.auto_scroll_var).pack(side="left")
        
    def create_status_bar(self):
        """Alt durum çubuğu"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", side="bottom")
        
        self.status_label = ttk.Label(status_frame, text="Hazır", relief="sunken")
        self.status_label.pack(fill="x", padx=5, pady=2)
        
    def load_selected_question(self):
        """Seçili soruyu yükle"""
        selection = self.question_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir soru seçin!")
            return
        
        # Mevcut PLC'yi durdur
        if self.plc and self.plc.running:
            self.stop_plc()
            time.sleep(0.5)
        
        # Yeni PLC oluştur
        plc_class = self.plc_classes[selection[0]]
        self.plc = plc_class()
        
        # Görsel arayüzü oluştur
        self.create_visual_interface()
        
        # Konsolu temizle
        self.clear_console()
        
        question_name = self.question_listbox.get(selection[0])
        self.console_print(f"\n{'='*50}")
        self.console_print(f"{question_name} YÜKLENDİ")
        self.console_print(f"{'='*50}\n")
        
        self.update_status(f"{question_name} yüklendi")
        
    def create_visual_interface(self):
        """Seçili soru için görsel arayüz oluştur"""
        # Eski içeriği temizle
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if not self.plc:
            return
        
        # Ana container
        main_visual = ttk.Frame(self.content_frame)
        main_visual.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input paneli
        if self.plc.inputs:
            input_frame = ttk.LabelFrame(main_visual, text="📥 GİRİŞLER (INPUTS)", padding=10)
            input_frame.pack(fill="x", pady=(0, 10))
            
            self.input_widgets = {}
            
            # İki sütunlu düzen
            row, col = 0, 0
            for input_name in self.plc.inputs:
                frame = ttk.Frame(input_frame)
                frame.grid(row=row, column=col, padx=10, pady=5, sticky="w")
                
                # Toggle button yerine checkbox + buton kombinasyonu
                if 'START' in input_name or 'STOP' in input_name:
                    btn = ttk.Button(frame, text=f"{input_name}", width=15,
                                   command=lambda n=input_name: self.pulse_input(n))
                    btn.pack()
                    self.input_widgets[input_name] = btn
                else:
                    var = tk.BooleanVar()
                    cb = ttk.Checkbutton(frame, text=input_name, variable=var,
                                       command=lambda n=input_name, v=var: self.update_input(n, v))
                    cb.pack()
                    self.input_widgets[input_name] = var
                
                col += 1
                if col > 2:
                    col = 0
                    row += 1
        
        # Output paneli
        if self.plc.outputs:
            output_frame = ttk.LabelFrame(main_visual, text="📤 ÇIKIŞLAR (OUTPUTS)", padding=10)
            output_frame.pack(fill="both", expand=True)
            
            self.output_widgets = {}
            
            # Özel görselleştirmeler
            if isinstance(self.plc, Question11_PLC):
                # Trafik ışığı için özel görsel
                self.create_traffic_light_visual(output_frame)
            elif isinstance(self.plc, Question13_PLC):
                # Yürüyen ışık için özel görsel
                self.create_running_light_visual(output_frame)
            elif isinstance(self.plc, Question8_PLC):
                # Taşıma bandı için özel görsel
                self.create_conveyor_visual(output_frame)
            else:
                # Standart LED gösterimi
                self.create_standard_output_visual(output_frame)
        
        # Counter ve Timer göstergeleri
        if self.plc.counters or self.plc.timers:
            info_frame = ttk.LabelFrame(main_visual, text="📊 SAYAÇLAR & ZAMANLYICILAR", padding=10)
            info_frame.pack(fill="x", pady=(10, 0))
            
            self.info_labels = {}
            
            # Counters
            if self.plc.counters:
                for name, counter in self.plc.counters.items():
                    label = ttk.Label(info_frame, text=f"{name}: 0/{counter.preset_value}")
                    label.pack(side="left", padx=10)
                    self.info_labels[f"counter_{name}"] = label
            
            # Timers
            if self.plc.timers:
                for name, timer in self.plc.timers.items():
                    label = ttk.Label(info_frame, text=f"{name}: 0.0/{timer.preset_time}s")
                    label.pack(side="left", padx=10)
                    self.info_labels[f"timer_{name}"] = label
    
    def create_standard_output_visual(self, parent):
        """Standart LED gösterimi"""
        led_frame = ttk.Frame(parent)
        led_frame.pack(expand=True)
        
        row, col = 0, 0
        for output_name in self.plc.outputs:
            # LED container
            led_container = ttk.Frame(led_frame)
            led_container.grid(row=row, column=col, padx=20, pady=20)
            
            # LED (Canvas)
            canvas = tk.Canvas(led_container, width=60, height=60, highlightthickness=0)
            canvas.pack()
            
            # LED çemberi
            led = canvas.create_oval(5, 5, 55, 55, fill='gray20', outline='black', width=2)
            
            # LED etiketi
            label = ttk.Label(led_container, text=output_name, font=('Arial', 10, 'bold'))
            label.pack()
            
            self.output_widgets[output_name] = (canvas, led)
            
            col += 1
            if col > 3:
                col = 0
                row += 1
    
    def create_traffic_light_visual(self, parent):
        """Trafik ışığı görselleştirmesi"""
        traffic_frame = ttk.Frame(parent)
        traffic_frame.pack(expand=True)
        
        # Araç ışığı
        vehicle_frame = ttk.LabelFrame(traffic_frame, text="🚗 ARAÇ IŞIKLARI", padding=10)
        vehicle_frame.grid(row=0, column=0, padx=20)
        
        v_canvas = tk.Canvas(vehicle_frame, width=80, height=220, bg='black')
        v_canvas.pack()
        
        # Kırmızı
        self.output_widgets['KIRMIZI_ARAC'] = (v_canvas, 
            v_canvas.create_oval(10, 10, 70, 70, fill='darkred', outline='gray'))
        v_canvas.create_text(40, 40, text="K", fill='white', font=('Arial', 20, 'bold'))
        
        # Sarı
        self.output_widgets['SARI_ARAC'] = (v_canvas,
            v_canvas.create_oval(10, 80, 70, 140, fill='#4B4B00', outline='gray'))
        v_canvas.create_text(40, 110, text="S", fill='white', font=('Arial', 20, 'bold'))
        
        # Yeşil
        self.output_widgets['YESIL_ARAC'] = (v_canvas,
            v_canvas.create_oval(10, 150, 70, 210, fill='darkgreen', outline='gray'))
        v_canvas.create_text(40, 180, text="Y", fill='white', font=('Arial', 20, 'bold'))
        
        # Yaya ışığı
        pedestrian_frame = ttk.LabelFrame(traffic_frame, text="🚶 YAYA IŞIKLARI", padding=10)
        pedestrian_frame.grid(row=0, column=1, padx=20)
        
        p_canvas = tk.Canvas(pedestrian_frame, width=80, height=150, bg='black')
        p_canvas.pack()
        
        # Kırmızı
        self.output_widgets['KIRMIZI_YAYA'] = (p_canvas,
            p_canvas.create_oval(10, 10, 70, 70, fill='darkred', outline='gray'))
        p_canvas.create_text(40, 40, text="DUR", fill='white', font=('Arial', 12, 'bold'))
        
        # Yeşil
        self.output_widgets['YESIL_YAYA'] = (p_canvas,
            p_canvas.create_oval(10, 80, 70, 140, fill='darkgreen', outline='gray'))
        p_canvas.create_text(40, 110, text="GEÇ", fill='white', font=('Arial', 12, 'bold'))
    
    def create_running_light_visual(self, parent):
        """Yürüyen ışık görselleştirmesi"""
        led_frame = ttk.Frame(parent)
        led_frame.pack(expand=True)
        
        # 6 LED yatay dizilim
        for i in range(1, 7):
            led_container = ttk.Frame(led_frame)
            led_container.pack(side="left", padx=10)
            
            canvas = tk.Canvas(led_container, width=80, height=80, highlightthickness=0)
            canvas.pack()
            
            # LED
            led = canvas.create_oval(10, 10, 70, 70, fill='gray20', outline='black', width=3)
            
            # Numara
            canvas.create_text(40, 40, text=str(i), fill='white', font=('Arial', 20, 'bold'))
            
            self.output_widgets[f'LED{i}'] = (canvas, led)
    
    def create_conveyor_visual(self, parent):
        """Taşıma bandı görselleştirmesi"""
        conveyor_frame = ttk.Frame(parent)
        conveyor_frame.pack(fill="both", expand=True)
        
        # Üst bilgi
        info_frame = ttk.Frame(conveyor_frame)
        info_frame.pack(fill="x", pady=10)
        
        self.product_label = ttk.Label(info_frame, text="Ürün Sayısı: 0/20", 
                                      font=('Arial', 14, 'bold'))
        self.product_label.pack()
        
        # Motor göstergeleri
        motor_frame = ttk.Frame(conveyor_frame)
        motor_frame.pack(expand=True)
        
        motor_info = [
            ("MOTOR1", "Taşıma Bandı", "#2196F3"),
            ("MOTOR2", "Motor 2\n(5 ürün)", "#4CAF50"),
            ("MOTOR3", "Motor 3\n(10 ürün)", "#FF9800"),
            ("MOTOR4", "Motor 4\n(15 ürün)", "#f44336")
        ]
        
        for i, (motor_name, label_text, color) in enumerate(motor_info):
            frame = ttk.Frame(motor_frame)
            frame.grid(row=i//2, column=i%2, padx=20, pady=20)
            
            canvas = tk.Canvas(frame, width=120, height=120, highlightthickness=0)
            canvas.pack()
            
            # Motor göstergesi
            motor = canvas.create_rectangle(10, 10, 110, 110, fill='gray20', outline=color, width=3)
            
            # Motor etiketi
            canvas.create_text(60, 60, text=label_text, fill='white', 
                              font=('Arial', 10, 'bold'), justify="center")
            
            self.output_widgets[motor_name] = (canvas, motor)
    
    def pulse_input(self, input_name):
        """START/STOP butonları için pulse sinyal"""
        if self.plc and self.plc.running:
            self.plc.inputs[input_name] = True
            self.console_print(f"[{datetime.now().strftime('%H:%M:%S')}] {input_name} basıldı")
            
            # 100ms sonra bırak
            self.root.after(100, lambda: setattr(self.plc.inputs, input_name, False))
    
    def update_input(self, input_name, var):
        """Input değerini güncelle"""
        if self.plc:
            self.plc.inputs[input_name] = var.get()
            state = "AKTİF" if var.get() else "PASİF"
            self.console_print(f"[{datetime.now().strftime('%H:%M:%S')}] {input_name}: {state}")
    
    def start_plc(self):
        """PLC'yi başlat"""
        if self.plc and not self.plc.running:
            self.plc.start()
            self.start_plc_btn.config(state="disabled")
            self.stop_plc_btn.config(state="normal")
            self.console_print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PLC BAŞLATILDI\n")
            self.update_status("PLC Çalışıyor")
    
    def stop_plc(self):
        """PLC'yi durdur"""
        if self.plc and self.plc.running:
            self.plc.stop()
            self.start_plc_btn.config(state="normal")
            self.stop_plc_btn.config(state="disabled")
            self.console_print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PLC DURDURULDU\n")
            self.update_status("PLC Durduruldu")
    
    def reset_plc(self):
        """PLC'yi sıfırla"""
        if self.plc:
            was_running = self.plc.running
            if was_running:
                self.stop_plc()
            
            # Tüm değerleri sıfırla
            for key in self.plc.inputs:
                self.plc.inputs[key] = False
            for key in self.plc.outputs:
                self.plc.outputs[key] = False
            
            # Input widget'larını sıfırla
            for name, widget in self.input_widgets.items():
                if isinstance(widget, tk.BooleanVar):
                    widget.set(False)
            
            self.console_print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PLC SIFIRLANDI\n")
            self.update_status("PLC Sıfırlandı")
    
    def update_gui(self):
        """GUI güncelleme döngüsü"""
        # Konsol güncellemesi
        try:
            while True:
                msg = self.console_queue.get_nowait()
                self.console_text.insert(tk.END, msg)
                if self.auto_scroll_var.get():
                    self.console_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Output güncellemesi
        if self.plc and hasattr(self, 'output_widgets'):
            for output_name, widget in self.output_widgets.items():
                if output_name in self.plc.outputs:
                    canvas, shape = widget
                    
                    if self.plc.outputs[output_name]:
                        # Output aktif - renkleri belirle
                        if 'KIRMIZI' in output_name:
                            color = 'red'
                        elif 'SARI' in output_name:
                            color = 'yellow'
                        elif 'YESIL' in output_name:
                            color = '#00FF00'
                        elif 'MOTOR' in output_name:
                            color = '#00FF00'
                        elif 'LED' in output_name:
                            color = '#FFD700'
                        else:
                            color = '#00FF00'
                        
                        canvas.itemconfig(shape, fill=color)
                    else:
                        # Output pasif
                        if 'KIRMIZI' in output_name:
                            canvas.itemconfig(shape, fill='darkred')
                        elif 'SARI' in output_name:
                            canvas.itemconfig(shape, fill='#4B4B00')
                        elif 'YESIL' in output_name:
                            canvas.itemconfig(shape, fill='darkgreen')
                        else:
                            canvas.itemconfig(shape, fill='gray20')
        
        # Counter ve Timer güncellemesi
        if self.plc and hasattr(self, 'info_labels'):
            # Counters
            if self.plc.counters:
                for name, counter in self.plc.counters.items():
                    key = f"counter_{name}"
                    if key in self.info_labels:
                        self.info_labels[key].config(
                            text=f"{name}: {counter.current_value}/{counter.preset_value}"
                        )
                        
                        # Özel güncelleme - taşıma bandı
                        if isinstance(self.plc, Question8_PLC) and hasattr(self, 'product_label'):
                            self.product_label.config(
                                text=f"Ürün Sayısı: {counter.current_value}/20"
                            )
            
            # Timers
            if self.plc.timers:
                for name, timer in self.plc.timers.items():
                    key = f"timer_{name}"
                    if key in self.info_labels:
                        elapsed = f"{timer.elapsed_time:.1f}" if timer.timing else "0.0"
                        self.info_labels[key].config(
                            text=f"{name}: {elapsed}/{timer.preset_time}s"
                        )
        
        # 50ms sonra tekrar güncelle
        self.root.after(50, self.update_gui)
    
    def setup_console_redirect(self):
        """Konsol çıktısını yakalama"""
        class ConsoleRedirect:
            def __init__(self, queue):
                self.queue = queue
            
            def write(self, text):
                self.queue.put(text)
            
            def flush(self):
                pass
        
        # sys.stdout'u yönlendir
        self.original_stdout = sys.stdout
        sys.stdout = ConsoleRedirect(self.console_queue)
    
    def console_print(self, text):
        """Konsola metin yaz"""
        self.console_queue.put(text + "\n")
    
    def clear_console(self):
        """Konsolu temizle"""
        self.console_text.delete(1.0, tk.END)
        self.console_print(f"Konsol temizlendi - {datetime.now().strftime('%H:%M:%S')}")
    
    def update_status(self, text):
        """Durum çubuğunu güncelle"""
        self.status_label.config(text=f"⚡ {text} - {datetime.now().strftime('%H:%M:%S')}")
    
    def run(self):
        """GUI'yi çalıştır"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Pencere kapatılırken"""
        if self.plc and self.plc.running:
            self.stop_plc()
        
        # stdout'u geri yükle
        sys.stdout = self.original_stdout
        
        self.root.destroy()

# Ana fonksiyon
def main():
    app = PLCVisualGUI()
    app.run()

if __name__ == "__main__":
    main()