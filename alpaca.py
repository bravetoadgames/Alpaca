import tkinter as tk
from tkinter import font, messagebox, ttk
import requests
import json
import threading
import os

# --- CONFIGURATION ---
BASE_URL = "http://localhost:11434"
THEME_BG = "#2b2b2b"      
THEME_FG = "#e1e1e1"      
ACCENT = "#3c3f41"        
INPUT_BG = "#3c3f41"
INPUT_DISABLED_BG = "#1e1e1e" 
SEND_BTN_BG = "#4e79a7"
DISABLED_FG = "#888888" 
JSON_FILE = "identities.json"

def load_identities():
    default_id = {"Helpful Assistant": "You are a helpful AI assistant."}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f: return json.load(f)
        except: return default_id
    return default_id

IDENTITIES = load_identities()

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Alpaca 1.2.8 - Model Sizes")
        self.root.geometry("1100x900")
        self.root.configure(bg=THEME_BG)

        self.selected_model = tk.StringVar()
        self.selected_identity = tk.StringVar()
        self.is_thinking = False 
        self.thinking_session = 0 
        self.chat_history = [] 

        self.setup_styles()
        self.setup_menu()
        self.setup_ui()
        
        self.selected_model.trace_add("write", self.update_status_bar)
        self.selected_identity.trace_add("write", self.update_status_bar)
        
        self.refresh_models()
        self.update_status_bar()
        self.input_field.focus_set()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", gripcount=0, background=ACCENT, troughcolor=THEME_BG, bordercolor=THEME_BG, darkcolor=THEME_BG, lightcolor=ACCENT, arrowcolor=THEME_FG)
        style.map("Vertical.TScrollbar", background=[('active', '#4e5052'), ('pressed', SEND_BTN_BG)], arrowcolor=[('active', 'white')])

    def setup_menu(self):
        self.menu_bar = tk.Menu(self.root, bg=THEME_BG, fg=THEME_FG)
        self.root.config(menu=self.menu_bar)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME_BG, fg=THEME_FG)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New Chat", command=self.clear_chat)
        
        self.model_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME_BG, fg=THEME_FG)
        self.menu_bar.add_cascade(label="Models", menu=self.model_menu)

        self.id_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME_BG, fg=THEME_FG)
        self.menu_bar.add_cascade(label="Identities", menu=self.id_menu)
        self.update_identity_menu()

    def set_ui_state(self, state):
        self.input_field.config(state=state)
        self.send_btn.config(state=state)
        if state == tk.DISABLED:
            self.send_btn.config(text="THINKING...")
        else:
            self.send_btn.config(text="SEND")
            self.input_field.focus_set()
            
        menu_state = tk.DISABLED if state == tk.DISABLED else tk.NORMAL
        try:
            self.menu_bar.entryconfig("File", state=menu_state)
            self.menu_bar.entryconfig("Models", state=menu_state)
            self.menu_bar.entryconfig("Identities", state=menu_state)
        except: pass

    def update_status_bar(self, *args):
        m = self.selected_model.get() or "None"
        # In de statusbar tonen we alleen de modelnaam (zonder de grootte-prefix)
        display_name = m.split(" - ")[-1] if " - " in m else m
        i = self.selected_identity.get() or "None"
        self.status_label.config(text=f" 🤖 Model: {display_name}  |  🎭 Identity: {i}")

    def update_identity_menu(self):
        self.id_menu.delete(0, tk.END)
        for name in IDENTITIES.keys():
            self.id_menu.add_radiobutton(label=name, variable=self.selected_identity, value=name)
        if IDENTITIES: 
            self.selected_identity.set(list(IDENTITIES.keys())[0])

    def refresh_models(self):
        try:
            r = requests.get(f"{BASE_URL}/api/tags", timeout=3)
            model_list = r.json().get("models", [])
            if not model_list:
                self.status_label.config(text=" ⚠️ No Models Found")
                return
            
            # Sorteren op grootte
            sorted_models = sorted(model_list, key=lambda x: x.get("size", 0))
            self.model_menu.delete(0, tk.END)
            
            for m in sorted_models:
                raw_name = m["name"]
                size_bytes = m.get("size", 0)
                size_gb = size_bytes / (1024**3)
                
                # Formatteren: " 4.2 GB - Llama3"
                # De padding aan de linkerkant helpt bij de uitlijning
                label_text = f"{size_gb:>5.1f} GB - {raw_name}"
                
                self.model_menu.add_radiobutton(
                    label=label_text, 
                    variable=self.selected_model, 
                    value=raw_name # We slaan alleen de echte naam op als waarde
                )
            
            if sorted_models:
                self.selected_model.set(sorted_models[0]["name"])
        except:
            self.status_label.config(text=" ⚠️ Ollama Offline")

    def setup_ui(self):
        self.status_frame = tk.Frame(self.root, bg=ACCENT, height=30)
        self.status_frame.pack(side="top", fill="x")
        self.status_label = tk.Label(self.status_frame, text="Initializing...", bg=ACCENT, fg="#abb2bf", font=("Segoe UI", 9))
        self.status_label.pack(side="left", padx=10)

        chat_container = tk.Frame(self.root, bg=THEME_BG)
        chat_container.pack(expand=True, fill="both", padx=10, pady=5)

        self.chat_display = tk.Text(chat_container, wrap=tk.WORD, bg=THEME_BG, fg=THEME_FG, font=("Ubuntu", 11), borderwidth=0, padx=15, pady=15, insertbackground="white")
        self.sb = ttk.Scrollbar(chat_container, orient="vertical", command=self.chat_display.yview, style="Vertical.TScrollbar")
        self.chat_display.configure(yscrollcommand=self.sb.set)
        self.sb.pack(side="right", fill="y")
        self.chat_display.pack(side="left", expand=True, fill="both")

        self.chat_display.tag_configure("header", foreground="#61afef", font=("Ubuntu", 11, "bold"))
        self.chat_display.tag_configure("thinking_style", foreground="#d19a66", font=("Ubuntu", 11, "italic"))
        self.chat_display.config(state=tk.DISABLED)

        self.input_frame = tk.Frame(self.root, bg=THEME_BG, pady=10)
        self.input_frame.pack(fill="x", padx=15, pady=10)
        
        self.input_field = tk.Entry(self.input_frame, bg=INPUT_BG, fg="white", font=("Ubuntu", 11), borderwidth=0, insertbackground="white", highlightthickness=1, highlightbackground=ACCENT, disabledbackground=INPUT_DISABLED_BG, disabledforeground=DISABLED_FG)
        self.input_field.pack(side="left", expand=True, fill="x", ipady=12, padx=(0, 10))
        self.input_field.bind("<Return>", self.start_query)
        
        self.send_btn = tk.Button(self.input_frame, text="SEND", command=self.start_query, bg=SEND_BTN_BG, fg="white", relief="flat", padx=10, disabledforeground=DISABLED_FG, width=12)
        self.send_btn.pack(side="right")

    def clear_chat(self):
        self.chat_history = []
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def start_query(self, event=None):
        query = self.input_field.get().strip()
        if not query or self.is_thinking: return "break"
        self.input_field.delete(0, tk.END)
        self.set_ui_state(tk.DISABLED)
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n\nYOU:\n", "header")
        self.chat_display.insert(tk.END, f"{query}\n")
        self.chat_display.mark_set("post_user_msg", "end-1c")
        self.chat_display.mark_gravity("post_user_msg", tk.LEFT)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        self.is_thinking = True
        self.thinking_session += 1
        self.animate_thinking(self.thinking_session)
        threading.Thread(target=self.call_ollama, args=(query,), daemon=True).start()
        return "break"

    def animate_thinking(self, sid, count=0):
        if not self.is_thinking or sid != self.thinking_session: return
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("post_user_msg", tk.END)
        dots = "." * (count % 4)
        clean_name = self.selected_identity.get().split('-')[0].split(':')[0]
        self.chat_display.insert(tk.END, f"\n{clean_name} is thinking{dots}", "thinking_style")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.root.after(400, lambda: self.animate_thinking(sid, count + 1))

    def call_ollama(self, query):
        try:
            payload = {
                "model": self.selected_model.get(),
                "messages": [{"role": "system", "content": IDENTITIES.get(self.selected_identity.get(), "")}] + self.chat_history + [{"role": "user", "content": query}],
                "stream": True
            }
            r = requests.post(f"{BASE_URL}/api/chat", json=payload, stream=True, timeout=120)
            full_reply = ""
            first_token = True
            for line in r.iter_lines():
                if not line: continue
                data = json.loads(line.decode('utf-8'))
                token = data.get("message", {}).get("content", "")
                full_reply += token
                if first_token:
                    self.is_thinking = False 
                    self.root.after(0, self.transition_to_ai)
                    first_token = False
                self.root.after(0, lambda t=token: self.append_ai_token(t))
                if data.get("done"): break
            self.chat_history.extend([{"role": "user", "content": query}, {"role": "assistant", "content": full_reply}])
            self.root.after(0, lambda: self.set_ui_state(tk.NORMAL))
        except Exception as e:
            self.is_thinking = False
            self.root.after(0, lambda: self.set_ui_state(tk.NORMAL))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    def transition_to_ai(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("post_user_msg", tk.END)
        full_name = self.selected_identity.get()
        clean_name = full_name.split('-')[0].split(':')[0].strip().upper()
        self.chat_display.insert(tk.END, f"\n\n{clean_name}:\n", "header")
        self.chat_display.insert(tk.END, "\n") 
        self.chat_display.config(state=tk.DISABLED)

    def append_ai_token(self, token):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, token)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()