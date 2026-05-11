import tkinter as tk
from tkinter import font, messagebox, ttk
import requests
import json
import threading
import pyperclip

# --- CONFIGURATION ---
BASE_URL = "http://localhost:11434"
THEME_BG = "#2b2b2b"
THEME_FG = "#e1e1e1"
CODE_BG = "#1e1e1e"
ACCENT = "#4a4a4a"
INPUT_BG = "#3c3f41"
SEND_BTN_BG = "#4e79a7"

# --- PRESET IDENTITIES ---
IDENTITIES = {
    "Helpful Assistant": "You are a helpful AI assistant.",
    "Adolf Hitler - German dictator": "You are the german dictator Adolf Hitler.",
    "Bindrmon - Pokemon-store owner": "You are a pokemon-store owner and are a little overweight. You can only think about pokemon cards and the rarity of them.",
    "Barry Botany - Expert gardener": "You are a botanicus who knows everything about all kinds of seeds, growing plants, generating produce and keeping them healthy.",
    "Bruce Willis - Hollywood actor": "You are Bruce Willis, the Hollywood actor. You are best friends with me and share all your Hollywood secrets whenever you can.",
    "Dungeon Master - Roleplaying genius": "You are a dungeonmaster, using the 5th edition Dungeons and Dragons ruleset. You are built for roleplay and can roll RPG dice.",
    "Python Expert - Programmer": "You are an expert Python developer. You provide concise, efficient, and well-documented code."
}

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Alpaca - An Ollama identity crisis")
        self.root.geometry("1000x900")
        self.root.configure(bg=THEME_BG)

        # Dropdown popup list options
        self.root.option_add('*TCombobox*Listbox.background', INPUT_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', THEME_FG)
        self.root.option_add('*TCombobox*Listbox.selectBackground', SEND_BTN_BG)

        self.available_models = []
        self.selected_model = tk.StringVar()
        self.selected_identity = tk.StringVar()
        self.is_thinking = False 
        self.full_response_buffer = ""

        self.normal_font = font.Font(family="Ubuntu", size=11)
        self.small_font = font.Font(family="Ubuntu", size=10)
        self.code_font = font.Font(family="Ubuntu Mono", size=11)

        self.setup_styles()
        self.setup_ui()
        self.refresh_models()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # --- Combobox Styling (Consistent Grey) ---
        self.style.map("TCombobox", 
            fieldbackground=[("readonly", INPUT_BG)],
            background=[("readonly", ACCENT)],
            foreground=[("readonly", THEME_FG)],
            arrowcolor=[("readonly", THEME_FG)]
        )
        self.style.configure("TCombobox", 
                             bordercolor=ACCENT, 
                             lightcolor=ACCENT, 
                             darkcolor=ACCENT,
                             selectbackground=INPUT_BG)

        # --- Scrollbar Styling ---
        self.style.configure("Vertical.TScrollbar", 
                             gripcount=0, background=ACCENT, darkcolor=THEME_BG, 
                             lightcolor=ACCENT, troughcolor=THEME_BG, 
                             bordercolor=THEME_BG, arrowcolor=THEME_FG)
        
        self.style.map("Vertical.TScrollbar",
            background=[('pressed', SEND_BTN_BG), ('active', "#5a5a5a")])

    def setup_ui(self):
        # --- Top bar (Model Selection) ---
        top_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        top_frame.pack(fill="x", padx=10)
        
        tk.Label(top_frame, text="Active Model:", bg=THEME_BG, fg=THEME_FG, font=self.normal_font).pack(side="left", padx=5)
        self.model_dropdown = ttk.Combobox(top_frame, textvariable=self.selected_model, state="readonly", width=25)
        self.model_dropdown.pack(side="left", padx=5)
        
        tk.Button(top_frame, text="Refresh List", command=self.refresh_models, 
                  bg=ACCENT, fg="white", relief="flat", padx=10, cursor="hand2").pack(side="left", padx=5)

        # --- Identity bar (Now with THEME_FG and no blue outline) ---
        id_frame = tk.Frame(self.root, bg=THEME_BG, pady=5)
        id_frame.pack(fill="x", padx=10)
        
        tk.Label(id_frame, text="System Identity:", bg=THEME_BG, fg=THEME_FG, font=self.normal_font).pack(side="left", padx=5)
        self.identity_dropdown = ttk.Combobox(id_frame, textvariable=self.selected_identity, state="readonly", width=35)
        self.identity_dropdown['values'] = list(IDENTITIES.keys())
        self.identity_dropdown.current(0)
        self.identity_dropdown.pack(side="left", padx=5)

        # --- Chat container ---
        chat_frame = tk.Frame(self.root, bg=THEME_BG)
        chat_frame.pack(expand=True, fill="both", padx=10, pady=5)

        self.chat_display = tk.Text(
            chat_frame, wrap=tk.WORD, bg=THEME_BG, fg=THEME_FG,
            insertbackground="white", font=self.normal_font,
            highlightthickness=0, borderwidth=0, padx=15, pady=15
        )
        
        self.scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_display.yview, style="Vertical.TScrollbar")
        self.chat_display.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.chat_display.pack(side="left", expand=True, fill="both")
        self.scrollbar.set(0.0, 1.0)

        self.chat_display.tag_configure("user", foreground="#81a2be", font=(None, 11, "bold"))
        self.chat_display.tag_configure("thinking", foreground="#f0c674", font=(None, 11, "italic"))
        self.chat_display.tag_configure("code_block", background=CODE_BG, font=self.code_font)

        # --- Input area ---
        input_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.input_field = tk.Entry(input_frame, bg=INPUT_BG, fg="white", insertbackground="white", font=self.normal_font, borderwidth=0)
        self.input_field.pack(side="left", expand=True, fill="x", ipady=12, padx=(0, 10))
        self.input_field.bind("<Return>", self.start_query)
        
        self.send_btn = tk.Button(input_frame, text="SEND", command=lambda: self.start_query(), 
                                  bg=SEND_BTN_BG, fg="white", font=(None, 10, "bold"), relief="flat", padx=25, pady=8, cursor="hand2")
        self.send_btn.pack(side="right")

    def refresh_models(self):
        try:
            response = requests.get(f"{BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                self.available_models = [m["name"] for m in models_data]
                self.model_dropdown['values'] = self.available_models
                if self.available_models: self.model_dropdown.current(0)
        except: 
            self.selected_model.set("Ollama offline")

    def animate_thinking(self, count=1):
        if not self.is_thinking: return
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("limit", tk.END)
        dots = "." * (count % 4) or "."
        identity_name = self.selected_identity.get()
        self.chat_display.insert(tk.END, f"\n{identity_name} is thinking{dots}", "thinking")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.root.after(400, lambda: self.animate_thinking(count + 1))

    def set_input_state(self, state):
        self.input_field.config(state=state)
        self.send_btn.config(state=state)
        if state == tk.NORMAL:
            self.input_field.focus_set()

    def start_query(self, event=None):
        query = self.input_field.get().strip()
        model = self.selected_model.get()
        identity_key = self.selected_identity.get()
        system_prompt = IDENTITIES.get(identity_key, "You are a helpful assistant.")
        
        self.input_field.delete(0, tk.END)
        if not query or not model or self.is_thinking or model == "Ollama offline": 
            return "break"
        
        self.set_input_state(tk.DISABLED)
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\nYOU:\n", "user")
        self.chat_display.insert(tk.END, f"{query}\n")
        self.chat_display.mark_set("limit", "end-1c")
        self.chat_display.mark_gravity("limit", tk.LEFT)
        self.chat_display.config(state=tk.DISABLED)
        
        self.is_thinking = True
        self.full_response_buffer = ""
        self.animate_thinking()
        
        threading.Thread(target=self.call_ollama_streaming, args=(query, model, system_prompt, identity_key), daemon=True).start()
        return "break"

    def call_ollama_streaming(self, prompt, model, system_prompt, identity_name):
        try:
            payload = {"model": model, "prompt": prompt, "system": system_prompt, "stream": True}
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, stream=True, timeout=180)
            
            first_token = True
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    token = data.get("response", "")
                    self.full_response_buffer += token
                    
                    if first_token:
                        self.is_thinking = False 
                        self.root.after(0, lambda: self.prepare_response_area(identity_name))
                        first_token = False
                    
                    self.root.after(0, lambda t=token: self.update_stream_ui(t))
                    
                    if data.get("done"):
                        self.root.after(0, self.finalize_response)
                        break
        except Exception as e:
            self.is_thinking = False
            self.root.after(0, lambda: self.set_input_state(tk.NORMAL))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    def prepare_response_area(self, identity_name):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("limit", tk.END)
        self.chat_display.insert(tk.END, f"\n\n{identity_name.upper()}:\n", "user")
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
        self.chat_display.delete("stream_start", tk.END)
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
                code_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else lines[0].strip()
                self.chat_display.insert(tk.END, f"\n{code_content}\n", "code_block")
                btn = tk.Button(self.chat_display, text="📋 Copy Code", 
                                command=lambda c=code_content: pyperclip.copy(c),
                                bg="#444", fg="#81a2be", font=("Arial", 8, "bold"), 
                                relief="flat", padx=5, pady=2, cursor="hand2")
                self.chat_display.window_create(tk.END, window=btn)
                self.chat_display.insert(tk.END, "\n")
            else:
                self.chat_display.insert(tk.END, part)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()