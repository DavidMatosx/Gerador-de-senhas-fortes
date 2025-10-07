#!/usr/bin/env python3
"""
Gerador de Senhas Fortes (Tkinter) - Persistente
Sem dependências externas.

Salva histórico em: ~/.gerador_senhas_history.json (por padrão, se autosave ativado ou se usar "Salvar Histórico")
Desenvolvido por David Matos
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import string
import secrets
import json
import os
from pathlib import Path

# Caminho para histórico (arquivo oculto na home do usuário)
HISTORY_FILE = Path.home() / ".gerador_senhas_history.json"
MAX_HISTORY_ITEMS = 200  # limite prático para evitar arquivos enormes

# Símbolos suportados
DEFAULT_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?/~`"

# Textos para pt/en
TEXTS = {
    "pt": {
        "select_lang": "Selecione o Idioma",
        "title": "Gerador de Senhas Fortes",
        "length": "Tamanho da Senha:",
        "include": "Incluir:",
        "uppercase": "Letras Maiúsculas",
        "lowercase": "Letras Minúsculas",
        "digits": "Números",
        "symbols": "Símbolos",
        "generate": "Gerar Senha",
        "copy": "Copiar",
        "placeholder": "Clique em Gerar Senha",
        "at_least_one": "Selecione pelo menos um tipo de caractere.",
        "saved": "Histórico salvo em:\n{}",
        "save_error": "Erro ao salvar histórico:\n{}",
        "confirm_clear": "Deseja limpar o histórico? Isso removerá os itens salvos localmente.",
        "cleared": "Histórico limpo.",
        "developed": "Desenvolvido por David Matos",
        "autosave": "Salvar histórico automaticamente",
        "save_history": "Salvar Histórico",
        "clear_history": "Limpar Histórico",
        "exit": "Sair",
        "copied": "Copiado para a área de transferência.",
        "no_history": "Nenhum item no histórico.",
        "warn_security": "Atenção: não salve senhas sensíveis em texto não criptografado.",
        "load_error": "Erro ao carregar histórico (ignorando):\n{}",
        "select_save_path": "Salvar histórico em outro arquivo (pressione Cancelar para manter padrão)"
    },
    "en": {
        "select_lang": "Select Language",
        "title": "Strong Password Generator",
        "length": "Password Length:",
        "include": "Include:",
        "uppercase": "Uppercase Letters",
        "lowercase": "Lowercase Letters",
        "digits": "Numbers",
        "symbols": "Symbols",
        "generate": "Generate Password",
        "copy": "Copy",
        "placeholder": "Click Generate Password",
        "at_least_one": "Select at least one character type.",
        "saved": "History saved to:\n{}",
        "save_error": "Error saving history:\n{}",
        "confirm_clear": "Clear history? This will remove locally saved items.",
        "cleared": "History cleared.",
        "developed": "Developed by David Matos",
        "autosave": "Autosave history",
        "save_history": "Save History",
        "clear_history": "Clear History",
        "exit": "Exit",
        "copied": "Copied to clipboard.",
        "no_history": "No items in history.",
        "warn_security": "Warning: don't store sensitive passwords in plaintext.",
        "load_error": "Error loading history (ignored):\n{}",
        "select_save_path": "Save history to another file (Cancel to keep default)"
    }
}


def ensure_at_least_one(chars_sets, length):
    """
    Garantir pelo menos um caractere de cada classe selecionada.
    chars_sets: lista de strings (cada string = conjunto de chars para essa classe)
    retorna lista de caracteres que garantem presença de cada classe
    """
    if length < len(chars_sets):
        raise ValueError("Length smaller than number of selected character classes.")
    chosen = [secrets.choice(s) for s in chars_sets]
    return chosen


def generate_password_logic(length, use_upper, use_lower, use_digits, use_symbols, symbols=DEFAULT_SYMBOLS):
    selected_sets = []
    if use_lower:
        selected_sets.append(string.ascii_lowercase)
    if use_upper:
        selected_sets.append(string.ascii_uppercase)
    if use_digits:
        selected_sets.append(string.digits)
    if use_symbols:
        selected_sets.append(symbols)

    if not selected_sets:
        raise ValueError("No character sets selected.")

    # garantir pelo menos um de cada
    guaranteed = ensure_at_least_one(selected_sets, length)

    # pool global
    pool = "".join(selected_sets)
    remaining_len = length - len(guaranteed)
    remaining = [secrets.choice(pool) for _ in range(remaining_len)]

    pwd_list = guaranteed + remaining

    # Fisher-Yates shuffle com secrets
    for i in range(len(pwd_list) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        pwd_list[i], pwd_list[j] = pwd_list[j], pwd_list[i]

    return "".join(pwd_list)


class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Senhas")
        self.root.geometry("+400+150")
        self.root.resizable(False, False)

        self.lang = tk.StringVar(value="pt")
        self.length_var = tk.IntVar(value=12)
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.autosave_var = tk.BooleanVar(value=False)
        self.history = []  # lista de strings
        self.history_file = HISTORY_FILE

        self.setup_language_screen()

        # tenta carregar histórico (silencioso)
        self._load_history_silently()

    def setup_language_screen(self):
        for w in self.root.winfo_children():
            w.destroy()

        t = TEXTS[self.lang.get()]
        lbl = tk.Label(self.root, text=t["select_lang"], font=("Arial", 12))
        lbl.pack(padx=12, pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=6)

        ttk.Button(frame, text="🇬🇧 English", command=lambda: self.set_language("en")).pack(side="left", padx=8)
        ttk.Button(frame, text="🇧🇷 Português", command=lambda: self.set_language("pt")).pack(side="left", padx=8)

    def set_language(self, code):
        self.lang.set(code)
        self.setup_main_ui()

    def setup_main_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        t = TEXTS[self.lang.get()]

        # Menu (Arquivo)
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label=t["save_history"], command=self.save_history_dialog)
        filemenu.add_command(label=t["clear_history"], command=self.clear_history)
        filemenu.add_separator()
        filemenu.add_command(label=t["exit"], command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

        # Título
        tk.Label(self.root, text=t["title"], font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(8, 6))

        # Tamanho
        tk.Label(self.root, text=t["length"]).grid(row=1, column=0, sticky="e", padx=(8,4))
        tk.Spinbox(self.root, from_=4, to=128, width=6, textvariable=self.length_var).grid(row=1, column=1, sticky="w")

        # Checkboxes (Include)
        tk.Label(self.root, text=t["include"]).grid(row=2, column=0, sticky="ne", padx=(8,4), pady=(6,0))
        chk_frame = tk.Frame(self.root)
        chk_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=(6,0))

        tk.Checkbutton(chk_frame, text=t["uppercase"], variable=self.upper_var).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(chk_frame, text=t["lowercase"], variable=self.lower_var).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(chk_frame, text=t["digits"], variable=self.digits_var).grid(row=0, column=1, sticky="w")
        tk.Checkbutton(chk_frame, text=t["symbols"], variable=self.symbols_var).grid(row=1, column=1, sticky="w")

        # Autosave checkbox
        tk.Checkbutton(self.root, text=t["autosave"], variable=self.autosave_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(4,0))

        # Generate button
        ttk.Button(self.root, text=t["generate"], command=self.on_generate).grid(row=4, column=0, columnspan=3, pady=8)

        # Password display entry
        self.password_var = tk.StringVar(value=t["placeholder"])
        self.password_entry = tk.Entry(self.root, textvariable=self.password_var, font=("Courier", 12), width=36, justify="center")
        self.password_entry.grid(row=5, column=0, columnspan=2, padx=8)

        ttk.Button(self.root, text=t["copy"], command=self.on_copy).grid(row=5, column=2, padx=(6,8))

        # History listbox + scrollbar
        lbl_hist = tk.Label(self.root, text="History")
        lbl_hist.grid(row=6, column=0, sticky="w", padx=8, pady=(10,0))
        self.history_listbox = tk.Listbox(self.root, width=54, height=8)
        self.history_listbox.grid(row=7, column=0, columnspan=3, padx=8)
        self.history_listbox.bind("<Double-Button-1>", self.on_history_double_click)
        # right-click menu for history items
        self._make_history_context_menu()

        # Rodapé (desenvolvido por)
        tk.Label(self.root, text=t["developed"], font=("Arial", 8), fg="gray").grid(row=8, column=0, columnspan=3, pady=(8,8))

        # populate history listbox with loaded items
        self._refresh_history_listbox()

    def _make_history_context_menu(self):
        self.ctx_menu = tk.Menu(self.root, tearoff=0)
        self.ctx_menu.add_command(label="Copy", command=self._copy_selected_history)
        self.ctx_menu.add_command(label="Delete", command=self._delete_selected_history)
        self.history_listbox.bind("<Button-3>", self._show_context_menu)  # right click

    def _show_context_menu(self, event):
        try:
            self.history_listbox.selection_clear(0, tk.END)
            idx = self.history_listbox.nearest(event.y)
            self.history_listbox.selection_set(idx)
            self.ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx_menu.grab_release()

    def _copy_selected_history(self):
        sel = self.history_listbox.curselection()
        if not sel:
            return
        pw = self.history_listbox.get(sel[0])
        self.root.clipboard_clear()
        self.root.clipboard_append(pw)
        self.root.update()
        messagebox.showinfo("Info", TEXTS[self.lang.get()]["copied"])

    def _delete_selected_history(self):
        sel = self.history_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        del self.history[idx]
        self._trim_history()
        self._refresh_history_listbox()
        # save if autosave
        if self.autosave_var.get():
            self._save_history_file(silent=True)

    def on_generate(self):
        t = TEXTS[self.lang.get()]
        use_upper = self.upper_var.get()
        use_lower = self.lower_var.get()
        use_digits = self.digits_var.get()
        use_symbols = self.symbols_var.get()
        length = int(self.length_var.get())

        if not (use_upper or use_lower or use_digits or use_symbols):
            messagebox.showwarning("Warn", t["at_least_one"])
            return

        try:
            pwd = generate_password_logic(length, use_upper, use_lower, use_digits, use_symbols)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.password_var.set(pwd)
        # adiciona ao histórico (no topo)
        self.history.insert(0, pwd)
        self._trim_history()
        self._refresh_history_listbox()

        if self.autosave_var.get():
            saved = self._save_history_file(silent=True)
            if not saved:
                # se falhar e autosave ativa, avisa (mas não interrompe)
                messagebox.showwarning("Warn", TEXTS[self.lang.get()]["save_error"].format("Could not save."))

    def on_copy(self):
        pw = self.password_var.get()
        if not pw:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pw)
        self.root.update()
        messagebox.showinfo("Info", TEXTS[self.lang.get()]["copied"])

    def on_history_double_click(self, event):
        sel = self.history_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        pw = self.history[idx]
        # copia e atualiza campo de senha
        self.password_var.set(pw)
        self.root.clipboard_clear()
        self.root.clipboard_append(pw)
        self.root.update()
        messagebox.showinfo("Info", TEXTS[self.lang.get()]["copied"])

    def _refresh_history_listbox(self):
        self.history_listbox.delete(0, tk.END)
        for item in self.history:
            self.history_listbox.insert(tk.END, item)
        if not self.history:
            # mostrar mensagem leve
            self.history_listbox.insert(tk.END, TEXTS[self.lang.get()]["no_history"])

    def _trim_history(self):
        if len(self.history) > MAX_HISTORY_ITEMS:
            self.history = self.history[:MAX_HISTORY_ITEMS]

    def save_history_dialog(self):
        # Pergunta confirmação ou permite salvar em outro arquivo
        t = TEXTS[self.lang.get()]
        if not self.history:
            messagebox.showinfo("Info", t["no_history"])
            return

        # Pergunta se deseja escolher outro caminho
        path_str = simpledialog.askstring("Save", t["select_save_path"], initialvalue=str(self.history_file))
        if path_str is None:  # cancel
            path = self.history_file
        else:
            path = Path(path_str).expanduser()

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Info", t["saved"].format(str(path)))
        except Exception as e:
            messagebox.showerror("Error", t["save_error"].format(str(e)))

    def clear_history(self):
        t = TEXTS[self.lang.get()]
        if messagebox.askyesno("Confirm", t["confirm_clear"]):
            self.history = []
            # tentar remover arquivo se existir
            try:
                if self.history_file.exists():
                    self.history_file.unlink()
            except Exception:
                pass
            self._refresh_history_listbox()
            messagebox.showinfo("Info", t["cleared"])

    def _save_history_file(self, silent=False):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            if not silent:
                messagebox.showinfo("Info", TEXTS[self.lang.get()]["saved"].format(str(self.history_file)))
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", TEXTS[self.lang.get()]["save_error"].format(str(e)))
            return False

    def _load_history_silently(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        # ensure strings
                        self.history = [str(x) for x in loaded if isinstance(x, (str, int, float))]
                        self._trim_history()
        except Exception as e:
            # load errors are non-fatal; show a warning in console and move on
            print(TEXTS[self.lang.get()]["load_error"].format(str(e)))

    # método para sobresalvar caminho (opcional)
    def set_history_file(self, path: Path):
        self.history_file = path


def main():
    root = tk.Tk()
    app = PasswordGeneratorApp(root)

    # exibir advertência de segurança na primeira execução (opcional)
    if messagebox.askyesno("Info", TEXTS[app.lang.get()]["warn_security"] + "\n\nOK to continue?"):
        pass

    root.mainloop()


if __name__ == "__main__":
    main()
