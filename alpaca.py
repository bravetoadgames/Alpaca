import tkinter as tk
from tkinter import font, scrolledtext, messagebox, ttk
import requests
import threading
import pyperclip

# --- CONFIGURATIE ---
BASE_URL = "http://localhost:11434"
THEME_BG = "#2b2b2b"   # Antraciet
THEME_FG = "#e1e1e1"   # Lichtgrijs text
CODE_BG = "#1e1e1e"    # Donkerder voor code
ACCENT = "#4a4a4a"     # Menu achtergrond
INPUT_BG = "#3c3f41"   # Invoerveld
SEND_BTN_BG = "#4e79a7" # Blauwachtige accentkleur

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Alpaca Ollama UI - Antraciet Editie")
        self.root.geometry("1000x850")
        self.root.configure(bg=THEME_BG)

        # Status variabelen
        self.available_models = []
        self.selected_model = tk.StringVar()
        self.is_thinking = False 

        # Fonts instellen (geoptimaliseerd voor Ubuntu)
        self.normal_font = font.Font(family="Ubuntu", size=11)
        self.code_font = font.Font(family="Ubuntu Mono", size=11)

        self.setup_ui()
        self.refresh_models()

    def setup_ui(self):
        # --- Top bar: Model selectie ---
        top_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        top_frame.pack(fill="x", padx=10)
        
        tk.Label(top_frame, text="Actief Model:", bg=THEME_BG, fg=THEME_FG, font=self.normal_font).pack(side="left", padx=5)
        
        # Styling voor de dropdown
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=INPUT_BG, background=ACCENT, foreground="white")
        
        self.model_dropdown = ttk.Combobox(top_frame, textvariable=self.selected_model, state="readonly", width=30)
        self.model_dropdown.pack(side="left", padx=5)
        
        self.refresh_btn = tk.Button(top_frame, text="Ververs Lijst", command=self.refresh_models, 
                                     bg=ACCENT, fg="white", relief="flat", padx=10, cursor="hand2")
        self.refresh_btn.pack(side="left", padx=5)

        # --- Chatvenster ---
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg=THEME_BG, fg=THEME_FG,
            insertbackground="white", font=self.normal_font,
            highlightthickness=0, borderwidth=0, padx=15, pady=15
        )
        self.chat_display.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Tekst tags voor styling
        self.chat_display.tag_configure("user", foreground="#81a2be", font=(None, 11, "bold"))
        self.chat_display.tag_configure("thinking", foreground="#f0c674", font=(None, 11, "italic"))
        self.chat_display.tag_configure("code_block", background=CODE_BG, font=self.code_font)

        # --- Input area ---
        input_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.input_field = tk.Entry(
            input_frame, bg=INPUT_BG, fg="white", 
            insertbackground="white", font=self.normal_font, borderwidth=0
        )
        self.input_field.pack(side="left", expand=True, fill="x", ipady=12, padx=(0, 10))
        
        # Bind ENTER key
        self.input_field.bind("<Return>", self.start_query)

        self.send_btn = tk.Button(
            input_frame, text="VERSTUUR", command=lambda: self.start_query(),
            bg=SEND_BTN_BG, fg="white", font=(None, 10, "bold"), relief="flat", padx=25, pady=8, cursor="hand2"
        )
        self.send_btn.pack(side="right")

    def refresh_models(self):
        """Haalt de lijst met beschikbare modellen op van de Ollama API."""
        try:
            response = requests.get(f"{BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                self.available_models = [m["name"] for m in models_data]
                self.model_dropdown['values'] = self.available_models
                if self.available_models:
                    self.model_dropdown.current(0)
            else:
                self.selected_model.set("Fout bij laden")
        except:
            self.selected_model.set("Ollama offline")

    def animate_thinking(self, count=1):
        """Toont de roulerende puntjes op een stabiele manier."""
        if not self.is_thinking:
            return

        self.chat_display.config(state=tk.NORMAL)
        
        # Verwijder de vorige animatie-regel vanaf de bladwijzer ('limit')
        self.chat_display.delete("limit", tk.END)
        
        dots = "." * (count % 4)
        if dots == "": dots = "."
        
        self.chat_display.insert(tk.END, f"\nOllama denkt na{dots}", "thinking")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

        # Plan de volgende frame van de animatie
        self.root.after(400, lambda: self.animate_thinking(count + 1))

    def start_query(self, event=None):
        """Verwerkt de vraag en start de achtergrond-thread."""
        query = self.input_field.get().strip()
        model = self.selected_model.get()
        
        if not query or not model or self.is_thinking or model == "Ollama offline":
            return "break" # Voorkomt extra newline in input bij ENTER
        
        # Gebruiker tekst toevoegen
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\nJIJ:\n", "user")
        self.chat_display.insert(tk.END, f"{query}\n")
        
        # Zet de 'limit' bladwijzer direct na de gebruikersvraag
        self.chat_display.mark_set("limit", "end-1c")
        self.chat_display.mark_gravity("limit", tk.LEFT)
        
        self.chat_display.config(state=tk.DISABLED)
        self.input_field.delete(0, tk.END)
        
        # Start de thinking status en thread
        self.is_thinking = True
        self.animate_thinking()
        
        thread = threading.Thread(target=self.call_ollama, args=(query, model))
        thread.daemon = True # Zorgt dat thread sluit als GUI sluit
        thread.start()
        
        return "break"

    def parse_and_highlight(self, text):
        """Splitst tekst en code-blokken, en voegt kopieerknoppen toe."""
        parts = text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Dit is een code-blok
                lines = part.split('\n')
                # Verwijder taal-identifier (zoals 'python' of 'bash') van de eerste regel
                code_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else lines[0].strip()
                
                self.chat_display.insert(tk.END, f"\n{code_content}\n", "code_block")
                
                # Voeg een interactieve kopieerknop toe onder de code
                copy_btn = tk.Button(
                    self.chat_display, text="📋 Kopieer Code", 
                    command=lambda c=code_content: pyperclip.copy(c),
                    bg="#444", fg="#81a2be", font=("Arial", 8, "bold"), 
                    relief="flat", padx=5, pady=2, cursor="hand2"
                )
                self.chat_display.window_create(tk.END, window=copy_btn)
                self.chat_display.insert(tk.END, "\n")
            else:
                # Normale tekst
                self.chat_display.insert(tk.END, part)

    def show_response(self, text):
        """Vervangt de 'denkt na' tekst door het uiteindelijke antwoord."""
        self.is_thinking = False
        self.chat_display.config(state=tk.NORMAL)
        
        # Verwijder de puntjes-regel
        self.chat_display.delete("limit", tk.END)

        self.chat_display.insert(tk.END, f"\nOLLAMA:\n", "user")
        self.parse_and_highlight(text)
        self.chat_display.insert(tk.END, "\n" + "-"*60 + "\n")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def call_ollama(self, prompt, model):
        """Verstuurt het verzoek naar de lokale API."""
        try:
            payload = {
                "model": model, 
                "prompt": prompt, 
                "stream": False
            }
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=180)
            
            if response.status_code == 200:
                result = response.json().get("response", "")
                self.root.after(0, lambda: self.show_response(result))
            else:
                self.is_thinking = False
                err = f"Fout: Server gaf code {response.status_code} terug."
                self.root.after(0, lambda: self.show_response(err))
        except Exception as e:
            self.is_thinking = False
            self.root.after(0, lambda: messagebox.showerror("Verbinding", f"Fout: {str(e)}"))

if __name__ == "__main__":
    root = tk.Tk()
    # Zorg dat het thema op Ubuntu ook de dropdown beïnvloedt
    try:
        root.tk.call('tk_setPalette', background=THEME_BG, foreground=THEME_FG)
    except:
        pass
    
    app = OllamaGUI(root)
    root.mainloop()