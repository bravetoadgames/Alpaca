import tkinter as tk
from tkinter import font, messagebox, ttk
import requests
import json
import threading
import pyperclip
import os

# --- CONFIGURATION ---
BASE_URL = "http://localhost:11434"
THEME_BG = "#2b2b2b"
THEME_FG = "#e1e1e1"
CODE_BG = "#1e1e1e"
ACCENT = "#4a4a4a"
INPUT_BG = "#3c3f41"
SEND_BTN_BG = "#4e79a7"
JSON_FILE = "identities.json"

def load_identities():
    """Laadt identiteiten uit JSON-bestand of maakt een default aan."""
    default_id = {"Helpful Assistant": "You are a helpful AI assistant."}
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f:
            json.dump(default_id, f, indent=4)
        return default_id
    try:
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("JSON Error", f"Fout bij laden van {JSON_FILE}:\n{str(e)}")
        return default_id

IDENTITIES = load_identities()

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Alpaca - UI Optimized & Memory Edition")
        self.root.geometry("1100x900")
        self.root.configure(bg=THEME_BG)

        # Forceer dark mode op de uitklaplijsten van de comboboxen
        self.root.option_add('*TCombobox*Listbox.background', INPUT_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', THEME_FG)
        self.root.option_add('*TCombobox*Listbox.selectBackground', SEND_BTN_BG)
        self.root.option_add('*TCombobox*Listbox.selectForeground', "white")

        self.available_models = []
        self.selected_model = tk.StringVar()
        self.selected_identity = tk.StringVar()
        self.is_thinking = False 
        self.thinking_session = 0 
        self.full_response_buffer = ""
        self.chat_history = [] 

        self.normal_font = font.Font(family="Ubuntu", size=11)
        self.code_font = font.Font(family="Ubuntu Mono", size=11)

        self.setup_styles()
        self.setup_ui()
        self.refresh_models()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Combobox Styling zonder witte randen
        self.style.configure("TCombobox", 
                             fieldbackground=INPUT_BG, 
                             background=ACCENT, 
                             foreground=THEME_FG, 
                             bordercolor=THEME_BG, 
                             darkcolor=THEME_BG, 
                             lightcolor=THEME_BG, 
                             arrowcolor=THEME_FG,
                             borderwidth=0)
        
        self.style.map("TCombobox", 
                       fieldbackground=[("readonly", INPUT_BG), ("focus", INPUT_BG)],
                       foreground=[("readonly", THEME_FG)])

        # Scrollbar styling
        self.style.configure("Vertical.TScrollbar", 
                             gripcount=0, 
                             background=ACCENT, 
                             troughcolor=THEME_BG, 
                             bordercolor=THEME_BG,
                             lightcolor=THEME_BG,
                             darkcolor=THEME_BG)

    def setup_ui(self):
        # --- BOVENSTE SECTIE (INSTELLINGEN) ---
        settings_container = tk.Frame(self.root, bg=THEME_BG, pady=15, padx=20)
        settings_container.pack(fill="x")

        # Kolom 1 (de dropdowns) moet uitbreidbaar zijn
        settings_container.grid_columnconfigure(1, weight=1)
        btn_width = 22 # Gelijkmatige breedte voor de knoppen

        # RIJ 0: MODEL
        tk.Label(settings_container, text="Model:", bg=THEME_BG, fg=THEME_FG, font=self.normal_font).grid(row=0, column=0, sticky="w", pady=5)
        
        self.model_dropdown = ttk.Combobox(settings_container, textvariable=self.selected_model, state="readonly")
        self.model_dropdown.grid(row=0, column=1, sticky="ew", padx=(15, 15), pady=5)
        
        tk.Button(settings_container, text="Refresh Models", command=self.refresh_models, 
                  bg=ACCENT, fg="white", relief="flat", width=btn_width, cursor="hand2", 
                  highlightthickness=0, bd=0).grid(row=0, column=2, sticky="e")

        # RIJ 1: IDENTITY
        tk.Label(settings_container, text="Identity:", bg=THEME_BG, fg=THEME_FG, font=self.normal_font).grid(row=1, column=0, sticky="w", pady=5)
        
        self.identity_dropdown = ttk.Combobox(settings_container, textvariable=self.selected_identity, state="readonly")
        self.identity_dropdown.grid(row=1, column=1, sticky="ew", padx=(15, 15), pady=5)
        self.identity_dropdown['values'] = list(IDENTITIES.keys())
        if IDENTITIES: self.identity_dropdown.current(0)
        
        self.clear_btn = tk.Button(settings_container, text="Clear Chat & Memory", command=self.clear_chat, 
                                   bg="#8b0000", fg="white", relief="flat", width=btn_width, cursor="hand2", 
                                   highlightthickness=0, bd=0)
        self.clear_btn.grid(row=1, column=2, sticky="e")

        # --- MIDDELSTE SECTIE (CHAT) ---
        chat_frame = tk.Frame(self.root, bg=THEME_BG)
        chat_frame.pack(expand=True, fill="both", padx=10, pady=5)

        self.chat_display = tk.Text(chat_frame, wrap=tk.WORD, bg=THEME_BG, fg=THEME_FG, 
                                    font=self.normal_font, borderwidth=0, padx=15, pady=15, 
                                    insertbackground="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_display.yview, style="Vertical.TScrollbar")
        self.chat_display.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.chat_display.pack(side="left", expand=True, fill="both")

        self.chat_display.tag_configure("user", foreground="#81a2be", font=(None, 11, "bold"))
        self.chat_display.tag_configure("thinking", foreground="#f0c674", font=(None, 11, "italic"))
        self.chat_display.tag_configure("code_block", background=CODE_BG, font=self.code_font)

        # --- ONDERSTE SECTIE (INPUT) ---
        input_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.input_field = tk.Entry(input_frame, bg=INPUT_BG, fg="white", font=self.normal_font, 
                                    borderwidth=0, insertbackground="white", highlightthickness=1, 
                                    highlightbackground=ACCENT)
        self.input_field.pack(side="left", expand=True, fill="x", ipady=12, padx=(0, 10))
        self.input_field.bind("<Return>", self.start_query)
        
        self.send_btn = tk.Button(input_frame, text="SEND", command=self.start_query, 
                                  bg=SEND_BTN_BG, fg="white", font=(None, 10, "bold"), 
                                  relief="flat", padx=25, pady=8, cursor="hand2",
                                  highlightthickness=0, bd=0)
        self.send_btn.pack(side="right")

    def clear_chat(self):
        self.chat_history = []
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def refresh_models(self):
        global IDENTITIES
        IDENTITIES = load_identities()
        self.identity_dropdown['values'] = list(IDENTITIES.keys())
        try:
            response = requests.get(f"{BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                self.available_models = [m["name"] for m in models_data]
                self.model_dropdown['values'] = self.available_models
                if self.available_models and not self.selected_model.get():
                    self.model_dropdown.current(0)
        except: 
            self.selected_model.set("Ollama offline")

    def animate_thinking(self, session_id, count=1):
        if not self.is_thinking or session_id != self.thinking_session: return
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("limit", tk.END)
        dots = "." * (count % 4) or "..."
        name = self.selected_identity.get().split(" - ")[0]
        self.chat_display.insert(tk.END, f"\n{name} is thinking{dots}", "thinking")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.root.after(400, lambda: self.animate_thinking(session_id, count + 1))

    def set_input_state(self, state):
        self.input_field.config(state=state)
        self.send_btn.config(state=state)
        self.clear_btn.config(state=state)
        if state == tk.NORMAL:
            self.input_field.focus_set()
            self.clear_btn.config(bg="#8b0000")
        else:
            self.clear_btn.config(bg="#444")

    def start_query(self, event=None):
        query = self.input_field.get().strip()
        model = self.selected_model.get()
        if not query or not model or self.is_thinking or model == "Ollama offline": return "break"
        
        identity_key = self.selected_identity.get()
        system_prompt = IDENTITIES.get(identity_key, "")
        
        self.input_field.delete(0, tk.END)
        self.set_input_state(tk.DISABLED)
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\nYOU:\n", "user")
        self.chat_display.insert(tk.END, f"{query}\n")
        self.chat_display.mark_set("limit", "end-1c")
        self.chat_display.mark_gravity("limit", tk.LEFT)
        self.chat_display.config(state=tk.DISABLED)
        
        self.is_thinking = True
        self.thinking_session += 1
        self.full_response_buffer = ""
        self.animate_thinking(self.thinking_session)
        
        threading.Thread(target=self.call_ollama_chat, args=(query, model, system_prompt), daemon=True).start()
        return "break"

    def call_ollama_chat(self, query, model, system_prompt):
        try:
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.chat_history)
            messages.append({"role": "user", "content": query})

            payload = {"model": model, "messages": messages, "stream": True}
            response = requests.post(f"{BASE_URL}/api/chat", json=payload, stream=True, timeout=180)
            
            first_token = True
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    token = data.get("message", {}).get("content", "")
                    self.full_response_buffer += token
                    
                    if first_token:
                        self.is_thinking = False 
                        self.root.after(0, self.prepare_response_area)
                        first_token = False
                    
                    self.root.after(0, lambda t=token: self.update_stream_ui(t))
                    
                    if data.get("done"):
                        self.chat_history.append({"role": "user", "content": query})
                        self.chat_history.append({"role": "assistant", "content": self.full_response_buffer})
                        if len(self.chat_history) > 20: self.chat_history = self.chat_history[-20:]
                        self.root.after(0, self.finalize_response)
                        break
        except Exception as e:
            self.is_thinking = False
            self.root.after(0, lambda: [self.set_input_state(tk.NORMAL), messagebox.showerror("Error", str(e))])

    def prepare_response_area(self):
        name = self.selected_identity.get().split(" - ")[0].upper()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("limit", tk.END)
        self.chat_display.insert(tk.END, f"\n\n{name}:\n", "user")
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)

    def update_stream_ui(self, token):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, token)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def finalize_response(self):
        self.chat_display.config(state=tk.NORMAL)
        # Reset de sectie na de vraag om dubbele tekst te voorkomen
        self.chat_display.delete("limit", tk.END)
        
        name = self.selected_identity.get().split(" - ")[0].upper()
        self.chat_display.insert(tk.END, f"\n\n{name}:\n", "user")
        self.chat_display.insert(tk.END, "\n")
        
        self.parse_and_highlight(self.full_response_buffer)
        self.chat_display.insert(tk.END, "\n" + "-"*60 + "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.set_input_state(tk.NORMAL)

    def parse_and_highlight(self, text):
        parts = text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                lines = part.split('\n')
                code = '\n'.join(lines[1:]).strip() if len(lines) > 1 else lines[0].strip()
                self.chat_display.insert(tk.END, f"\n{code}\n", "code_block")
                btn = tk.Button(self.chat_display, text="📋 Copy Code", command=lambda c=code: pyperclip.copy(c), 
                                bg="#444", fg="#81a2be", font=("Arial", 8, "bold"), relief="flat", 
                                padx=5, pady=2, cursor="hand2", highlightthickness=0, bd=0)
                self.chat_display.window_create(tk.END, window=btn)
                self.chat_display.insert(tk.END, "\n")
            else:
                self.chat_display.insert(tk.END, part)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()