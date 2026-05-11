import tkinter as tk
from tkinter import font, scrolledtext, messagebox, ttk
import requests
import json
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
        self.root.title("Alpaca Ollama UI - Streaming Edition")
        self.root.geometry("1000x850")
        self.root.configure(bg=THEME_BG)

        # Status variabelen
        self.available_models = []
        self.selected_model = tk.StringVar()
        self.is_thinking = False 
        self.full_response_buffer = ""

        # Fonts
        self.normal_font = font.Font(family="Ubuntu", size=11)
        self.code_font = font.Font(family="Ubuntu Mono", size=11)

        self.setup_ui()
        self.refresh_models()

    def setup_ui(self):
        # Top bar
        top_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        top_frame.pack(fill="x", padx=10)
        tk.Label(top_frame, text="Actief Model:", bg=THEME_BG, fg=THEME_FG, font=self.normal_font).pack(side="left", padx=5)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=INPUT_BG, background=ACCENT, foreground="white")
        self.model_dropdown = ttk.Combobox(top_frame, textvariable=self.selected_model, state="readonly", width=30)
        self.model_dropdown.pack(side="left", padx=5)
        
        tk.Button(top_frame, text="Ververs Lijst", command=self.refresh_models, 
                  bg=ACCENT, fg="white", relief="flat", padx=10, cursor="hand2").pack(side="left", padx=5)

        # Chatvenster
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg=THEME_BG, fg=THEME_FG,
            insertbackground="white", font=self.normal_font,
            highlightthickness=0, borderwidth=0, padx=15, pady=15
        )
        self.chat_display.pack(expand=True, fill="both", padx=10, pady=5)
        
        self.chat_display.tag_configure("user", foreground="#81a2be", font=(None, 11, "bold"))
        self.chat_display.tag_configure("thinking", foreground="#f0c674", font=(None, 11, "italic"))
        self.chat_display.tag_configure("code_block", background=CODE_BG, font=self.code_font)

        # Input area
        input_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        input_frame.pack(fill="x", padx=10, pady=10)
        self.input_field = tk.Entry(input_frame, bg=INPUT_BG, fg="white", insertbackground="white", font=self.normal_font, borderwidth=0)
        self.input_field.pack(side="left", expand=True, fill="x", ipady=12, padx=(0, 10))
        self.input_field.bind("<Return>", self.start_query)
        tk.Button(input_frame, text="VERSTUUR", command=lambda: self.start_query(), bg=SEND_BTN_BG, fg="white", font=(None, 10, "bold"), relief="flat", padx=25, pady=8, cursor="hand2").pack(side="right")

    def refresh_models(self):
        try:
            response = requests.get(f"{BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                self.available_models = [m["name"] for m in models_data]
                self.model_dropdown['values'] = self.available_models
                if self.available_models: self.model_dropdown.current(0)
        except: self.selected_model.set("Ollama offline")

    def animate_thinking(self, count=1):
        if not self.is_thinking: return
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("limit", tk.END)
        dots = "." * (count % 4) or "."
        self.chat_display.insert(tk.END, f"\nOllama denkt na{dots}", "thinking")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.root.after(400, lambda: self.animate_thinking(count + 1))

    def start_query(self, event=None):
        query = self.input_field.get().strip()
        model = self.selected_model.get()
        if not query or not model or self.is_thinking or model == "Ollama offline": return "break"
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\nJIJ:\n", "user")
        self.chat_display.insert(tk.END, f"{query}\n")
        self.chat_display.mark_set("limit", "end-1c")
        self.chat_display.mark_gravity("limit", tk.LEFT)
        self.chat_display.config(state=tk.DISABLED)
        self.input_field.delete(0, tk.END)
        
        self.is_thinking = True
        self.full_response_buffer = ""
        self.animate_thinking()
        
        threading.Thread(target=self.call_ollama_streaming, args=(query, model), daemon=True).start()
        return "break"

    def call_ollama_streaming(self, prompt, model):
        try:
            payload = {"model": model, "prompt": prompt, "stream": True}
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, stream=True, timeout=180)
            
            first_token = True
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    token = data.get("response", "")
                    self.full_response_buffer += token
                    
                    if first_token:
                        self.is_thinking = False 
                        self.root.after(0, self.prepare_response_area)
                        first_token = False
                    
                    self.root.after(0, lambda t=token: self.update_stream_ui(t))
                    
                    if data.get("done"):
                        self.root.after(0, self.finalize_response)
                        break
        except Exception as e:
            self.is_thinking = False
            self.root.after(0, lambda: messagebox.showerror("Fout", str(e)))

    def prepare_response_area(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("limit", tk.END)
        self.chat_display.insert(tk.END, f"\nOLLAMA:\n", "user")
        # Fix: Voeg een lege regel toe en markeer DAAR de start van de stream
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.mark_set("stream_start", "end-1c")
        self.chat_display.mark_gravity("stream_start", tk.LEFT)
        self.chat_display.config(state=tk.DISABLED)

    def update_stream_ui(self, token):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, token)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def finalize_response(self):
        self.chat_display.config(state=tk.NORMAL)
        # Verwijder alles vanaf de stream_start markering tot het absolute einde
        self.chat_display.delete("stream_start", tk.END)
        # Plaats de buffer geformatteerd terug
        self.parse_and_highlight(self.full_response_buffer)
        self.chat_display.insert(tk.END, "\n" + "-"*60 + "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def parse_and_highlight(self, text):
        # Dezelfde logica voor code-blokken en kopieerknoppen
        parts = text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                lines = part.split('\n')
                code_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else lines[0].strip()
                self.chat_display.insert(tk.END, f"\n{code_content}\n", "code_block")
                btn = tk.Button(self.chat_display, text="📋 Kopieer Code", 
                                command=lambda c=code_content: pyperclip.copy(c),
                                bg="#444", fg="#81a2be", font=("Arial", 8, "bold"), relief="flat", padx=5, pady=2, cursor="hand2")
                self.chat_display.window_create(tk.END, window=btn)
                self.chat_display.insert(tk.END, "\n")
            else:
                self.chat_display.insert(tk.END, part)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()