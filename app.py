import customtkinter as ctk
import random

# إعداد المظهر العام للنظام (تصميم فاخر يناسب الألعاب التفاعلية والكازينوهات)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("gold")

class LiraApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Lira Platform - امبراطورية الأرقام")
        self.geometry("1000x700")
        self.resizable(False, False)

        # متغيرات الحساب
        self.current_user = ctk.StringVar(value="")
        self.user_balance = ctk.DoubleVar(value=150.0) # الرصيد الافتتاحي تجريبي

        # بدء عرض الصفحة الأولى (تسجيل الدخول - خلف الكواليس)
        self.show_login_page()

    def clear_window(self):
        """مسح محتويات النافذة الحالية للانتقال بسلاسة للصفحة التالية"""
        for widget in self.winfo_children():
            widget.destroy()

    # ==========================================
    # الصفحة الأولى: تسجيل الدخول (Lira Login)
    # ==========================================
    def show_login_page(self):
        self.clear_window()

        login_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=20)
        login_frame.place(relx=0.5, rely=0.5, anchor="center", width=450, height=500)

        title_label = ctk.CTkLabel(login_frame, text="LIRA", font=("Arial Black", 36), text_color="#ffd700")
        title_label.pack(pady=(40, 10))

        sub_label = ctk.CTkLabel(login_frame, text="النظام التفاعلي الملكي", font=("Arial", 14), text_color="#aaaaaa")
        sub_label.pack(pady=(0, 30))

        self.username_entry = ctk.CTkEntry(login_frame, placeholder_text="اسم المستخدم", width=320, height=45, font=("Arial", 14))
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(login_frame, placeholder_text="كلمة المرور", show="*", width=320, height=45, font=("Arial", 14))
        self.password_entry.pack(pady=10)

        self.error_label = ctk.CTkLabel(login_frame, text="", font=("Arial", 12), text_color="#ff4444")
        self.error_label.pack(pady=5)

        login_btn = ctk.CTkButton(login_frame, text="تسجيل الدخول", fg_color="#d4af37", hover_color="#aa8c2c",
                                  text_color="#000000", font=("Arial-Bold", 16), width=320, height=45,
                                  command=self.validate_login)
        login_btn.pack(pady=(20, 10))

    def validate_login(self):
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get().strip()

        if user == "" or pwd == "":
            self.error_label.configure(text="الرجاء إدخال اسم المستخدم وكلمة المرور!")
        else:
            self.current_user.set(user)
            self.show_main_dashboard()

    # ==========================================
    # الصفحة الثانية: لوحة التحكم والـ 8 أيقونات الفاخرة
    # ==========================================
    def show_main_dashboard(self):
        self.clear_window()

        header_frame = ctk.CTkFrame(self, height=80, fg_color="#121212", corner_radius=0)
        header_frame.pack(side="top", fill="x")

        user_info = ctk.CTkLabel(header_frame, text=f"المستخدم: {self.current_user.get()}  |  الرصيد: ${self.user_balance.get():.2f}", 
                                 font=("Arial-Bold", 16), text_color="#ffd700")
        user_info.pack(side="left", padx=25)

        refresh_btn = ctk.CTkButton(header_frame, text="تحديث الألعاب", fg_color="#333333", hover_color="#444444",
                                    width=120, height=35, command=self.show_main_dashboard)
        refresh_btn.pack(side="right", padx=10)

        whatsapp_btn = ctk.CTkButton(header_frame, text="شراء رصيد (واتساب)", fg_color="#25D366", hover_color="#1EBE5D",
                                     text_color="#ffffff", width=150, height=35, 
                                     command=lambda: print("رقم الواتساب للتواصل: 96176030208"))
        whatsapp_btn.pack(side="right", padx=10)

        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=40, pady=20)

        games_data = [
            ("اللعبة الملكية (3D)", self.open_royal_game),
            ("روليت الكازينو الملكي", self.open_roulette_game),
            ("لعبة الحظ السريع", lambda: print("قريباً")),
            ("سباق الخيل التفاعلي", lambda: print("قريباً")),
            ("عجلة الثروة الكبرى", lambda: print("قريباً")),
            ("صناديق المفاجآت الذهبية", lambda: print("قريباً")),
            ("تحدي الأرقام الفائزة", lambda: print("قريباً")),
            ("البوكر الملكي المباشر", lambda: print("قريباً"))
        ]

        for i, (game_name, command_func) in enumerate(games_data):
            row = i // 4
            col = i % 4

            card = ctk.CTkFrame(grid_frame, fg_color="#1f1f1f", corner_radius=15, border_width=2, border_color="#333333")
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            icon_btn = ctk.CTkButton(card, text="🎮\n[ LOGO ]", font=("Arial", 22), 
                                     fg_color="#262626", hover_color="#383838", text_color="#ffd700",
                                     corner_radius=12, command=command_func)
            icon_btn.pack(expand=True, fill="both", padx=10, pady=(10, 5))

            lbl = ctk.CTkLabel(card, text=game_name, font=("Arial-Bold", 13), text_color="#ffffff")
            lbl.pack(pady=(0, 10))

        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)
        for i in range(2):
            grid_frame.rowconfigure(i, weight=1)

    # ==========================================
    # اللعبة الأولى: اللعبة الملكية (3D Style)
    # ==========================================
    def open_royal_game(self):
        self.clear_window()

        back_btn = ctk.CTkButton(self, text="⬅ العودة للرئيسية", fg_color="#333333", width=130, command=self.show_main_dashboard)
        back_btn.pack(anchor="nw", padx=20, pady=20)

        title = ctk.CTkLabel(self, text="👑 اللعبة الملكية الحصرية (3D)", font=("Arial-Bold", 24), text_color="#ffd700")
        title.pack(pady=10)

        game_box = ctk.CTkFrame(self, fg_color="#181818", corner_radius=20, border_width=3, border_color="#d4af37")
        game_box.pack(expand=True, fill="both", padx=50, pady=20)

        display_frame = ctk.CTkFrame(game_box, fg_color="transparent")
        display_frame.pack(expand=True)

        self.digit_labels = []
        for i in range(5):
            box = ctk.CTkLabel(display_frame, text="?", font=("Arial Black", 32), text_color="#ffd700",
                               fg_color="#252525", corner_radius=10, width=80, height=80)
            box.grid(row=0, column=i, padx=10)
            self.digit_labels.append(box)

        separator = ctk.CTkLabel(display_frame, text="⬅", font=("Arial", 28), text_color="#d4af37")
        separator.grid(row=0, column=5, padx=20)

        self.winning_box = ctk.CTkLabel(display_frame, text="الرقم\nالرابح", font=("Arial-Bold", 16), text_color="#000000",
                                       fg_color="#d4af37", corner_radius=12, width=100, height=100)
        self.winning_box.grid(row=0, column=6, padx=10)

        self.start_draw_btn = ctk.CTkButton(game_box, text="بدء السحب الآلي وإعلان الرقم الرابح", font=("Arial-Bold", 16),
                                            fg_color="#d4af37", hover_color="#aa8c2c", text_color="#000000",
                                            width=300, height=50, command=self.start_royal_draw)
        self.start_draw_btn.pack(pady=30)

    def start_royal_draw(self):
        self.start_draw_btn.configure(state="disabled", text="جاري حجز الأرقام وبدء العد السريع...")
        
        def animate_numbers(counter=0):
            if counter < 30:
                for box in self.digit_labels:
                    box.configure(text=str(random.randint(0, 9)))
                self.winning_box.configure(text=str(random.randint(0, 9)))
                self.after(100, lambda: animate_numbers(counter + 1))
            else:
                winning_number = "7" 
                for box in self.digit_labels:
                    box.configure(text=winning_number, fg_color="#006400")
                
                self.winning_box.configure(text=winning_number, fg_color="#ffcc00")
                
                new_bal = self.user_balance.get() + 200.0
                self.user_balance.set(new_bal)

                win_popup = ctk.CTkLabel(self, text=f"🎉 مبروك! لقد ربح الرقم الرابح {winning_number} وتم تحويل جائزة 200$ فوراً لحسابك!",
                                         font=("Arial-Bold", 16), text_color="#00ff00", fg_color="#111111", corner_radius=10)
                win_popup.place(relx=0.5, rely=0.15, anchor="center")

                self.start_draw_btn.configure(state="normal", text="إعادة السحب")

        animate_numbers()

    # ==========================================
    # اللعبة الثانية: روليت الكازينو العالمي (Roulette)
    # ==========================================
    def open_roulette_game(self):
        self.clear_window()

        back_btn = ctk.CTkButton(self, text="⬅ العودة للرئيسية", fg_color="#333333", width=130, command=self.show_main_dashboard)
        back_btn.pack(anchor="nw", padx=20, pady=20)

        title = ctk.CTkLabel(self, text="🎰 طاولة روليت الكازينو العالمية (Live Simulation)", font=("Arial-Bold", 24), text_color="#ffd700")
        title.pack(pady=10)

        roulette_box = ctk.CTkFrame(self, fg_color="#0f2b1d", corner_radius=20, border_width=3, border_color="#d4af37")
        roulette_box.pack(expand=True, fill="both", padx=40, pady=20)

        self.wheel_display = ctk.CTkLabel(roulette_box, text="🎡 [ قرص الروليت الدوار ]\nجاهز للمراهنة", 
                                          font=("Arial-Bold", 20), text_color="#ffffff",
                                          fg_color="#081810", corner_radius=15, width=400, height=180)
        self.wheel_display.pack(pady=30)

        bet_panel = ctk.CTkFrame(roulette_box, fg_color="transparent")
        bet_panel.pack(pady=10)

        red_btn = ctk.CTkButton(bet_panel, text="رهان أحمر (Red)", fg_color="#cc0000", hover_color="#990000", width=150, height=45,
                                command=lambda: self.spin_roulette("أحمر"))
        red_btn.grid(row=0, column=0, padx=15)

        black_btn = ctk.CTkButton(bet_panel, text="رهان أسود (Black)", fg_color="#222222", hover_color="#000000", width=150, height=45,
                                  command=lambda: self.spin_roulette("أسود"))
        black_btn.grid(row=0, column=1, padx=15)

        self.roulette_result_label = ctk.CTkLabel(roulette_box, text="", font=("Arial-Bold", 16), text_color="#ffd700")
        self.roulette_result_label.pack(pady=20)

    def spin_roulette(self, bet_choice):
        self.wheel_display.configure(text="🎡 الكرة تدور بسرعة داخل القرص...\nحظاً سعيداً!")
        self.roulette_result_label.configure(text="")

        def finish_spin():
            winning_num = random.randint(0, 36)
            winning_color = "أحمر" if winning_num % 2 == 0 and winning_num != 0 else "أسود"
            if winning_num == 0:
                winning_color = "أخضر (صفر الكازينو)"

            self.wheel_display.configure(text=f"🎯 استقرت الكرة على الرقم: {winning_num}\nاللون: {winning_color}")

            if bet_choice == winning_color:
                profit = 50.0
                self.user_balance.set(self.user_balance.get() + profit)
                self.roulette_result_label.configure(text=f"🎉 مبروك! لقد ربحت رهانتك وحصلت على ${profit}!", text_color="#00ff00")
            else:
                loss = 25.0
                self.user_balance.set(max(0.0, self.user_balance.get() - loss))
                self.roulette_result_label.configure(text=f"❌ هاردلك! لقد خسر الرهان بقيمة ${loss}.", text_color="#ff4444")

        self.after(2500, finish_spin)

if __name__ == "__main__":
    app = LiraApp()
    app.mainloop()
