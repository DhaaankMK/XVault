"""
X-Vault :: main.py
Interface principal — CustomTkinter dark, profissional.
Ponto de entrada. Verifica admin, gerencia todas as telas.
"""

import sys
import os
import threading
import time
from pathlib import Path

# ── Verificar admin ANTES de importar qualquer coisa pesada ──────────────────
def _check_admin_early():
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            result = messagebox.askyesno(
                "X-Vault — Permissão Necessária",
                "⚠️  X-Vault precisa de privilégios de Administrador para\n"
                "proteger seus arquivos corretamente.\n\n"
                "Deseja reiniciar como Administrador agora?",
                icon="warning"
            )
            root.destroy()
            if result:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable,
                    " ".join(f'"{a}"' for a in sys.argv),
                    None, 1
                )
            sys.exit(0)
    except Exception:
        pass  # Não-Windows — continua normalmente

if sys.platform == "win32":
    _check_admin_early()

# ── Imports principais ───────────────────────────────────────────────────────
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

# Módulos do X-Vault
sys.path.insert(0, str(Path(__file__).parent))
from auth_manager    import AuthManager, AuthLockedError, AuthWrongPasswordError
from crypto_engine   import CryptoEngine
from stealth_module  import StealthModule, is_admin
from settings_manager import SettingsManager

# ── Constantes de UI ─────────────────────────────────────────────────────────
APP_NAME    = "X-Vault"
APP_VERSION = "1.0.0"
WIN_W, WIN_H = 520, 680

# Paleta
C_BG        = "#0d0d0f"
C_SURFACE   = "#141418"
C_SURFACE2  = "#1c1c23"
C_BORDER    = "#2a2a35"
C_ACCENT    = "#00d4aa"
C_ACCENT2   = "#0099ff"
C_DANGER    = "#ff4455"
C_WARNING   = "#ffaa00"
C_TEXT      = "#e8e8f0"
C_MUTED     = "#6b6b80"
C_SUCCESS   = "#00d4aa"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class XVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.auth     = AuthManager()
        self.settings = SettingsManager()
        self._password_cache = None   # senha em memória (nunca em disco)
        self._lock_timer = None

        self._setup_window()
        self._build_ui()
        self._show_initial_screen()

    # ─── Janela ───────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.title(APP_NAME)
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)

        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - WIN_W) // 2
        y = (self.winfo_screenheight() - WIN_H) // 2
        self.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

        # Ícone (se existir)
        icon = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon.exists():
            try: self.iconbitmap(str(icon))
            except: pass

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── Container principal ──────────────────────────────────────────────────
    def _build_ui(self):
        # Header sempre visível
        self._header = self._make_header()
        self._header.pack(fill="x")

        # Separador
        ctk.CTkFrame(self, height=1, fg_color=C_BORDER).pack(fill="x")

        # Container de conteúdo (trocável)
        self._content = ctk.CTkFrame(self, fg_color=C_BG)
        self._content.pack(fill="both", expand=True, padx=0, pady=0)

        # Status bar
        self._status_var = tk.StringVar(value="")
        self._statusbar  = ctk.CTkLabel(
            self, textvariable=self._status_var,
            font=ctk.CTkFont("Courier New", 11),
            text_color=C_MUTED, fg_color=C_SURFACE,
            anchor="w", height=28
        )
        self._statusbar.pack(fill="x", side="bottom")

    def _make_header(self) -> ctk.CTkFrame:
        fr = ctk.CTkFrame(self, fg_color=C_SURFACE, height=64, corner_radius=0)
        fr.pack_propagate(False)

        # Logo + nome
        logo_fr = ctk.CTkFrame(fr, fg_color="transparent")
        logo_fr.pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            logo_fr, text="◈", font=ctk.CTkFont("Segoe UI", 28, "bold"),
            text_color=C_ACCENT, fg_color="transparent"
        ).pack(side="left", padx=(0, 8))

        name_fr = ctk.CTkFrame(logo_fr, fg_color="transparent")
        name_fr.pack(side="left")
        ctk.CTkLabel(
            name_fr, text="X-VAULT",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=C_TEXT
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_fr, text="Proteção de Dados",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=C_MUTED
        ).pack(anchor="w")

        # Badge admin
        if is_admin():
            ctk.CTkLabel(
                fr, text="🛡 ADMIN", font=ctk.CTkFont("Segoe UI", 10, "bold"),
                text_color=C_ACCENT, fg_color=C_SURFACE2,
                corner_radius=4, padx=8, pady=4
            ).pack(side="right", padx=16, pady=18)
        else:
            ctk.CTkLabel(
                fr, text="⚠ SEM ADMIN", font=ctk.CTkFont("Segoe UI", 10, "bold"),
                text_color=C_WARNING, fg_color=C_SURFACE2,
                corner_radius=4, padx=8, pady=4
            ).pack(side="right", padx=16, pady=18)

        return fr

    # ─── Navegação entre telas ────────────────────────────────────────────────
    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _show_initial_screen(self):
        if not self.auth.has_password():
            self._show_setup_screen()
        else:
            self._show_login_screen()

    # ════════════════════════════════════════════════════════════════════════════
    # TELA: Configuração inicial (primeiro uso)
    # ════════════════════════════════════════════════════════════════════════════
    def _show_setup_screen(self):
        self._clear_content()
        fr = self._content

        self._section_label(fr, "CONFIGURAÇÃO INICIAL")
        self._info_label(fr,
            "Primeira execução detectada.\n"
            "Crie uma senha mestra forte para proteger seu cofre."
        )

        ctk.CTkFrame(fr, height=16, fg_color="transparent").pack()

        # Campo: nova senha
        ctk.CTkLabel(fr, text="SENHA MESTRA", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=C_MUTED, anchor="w").pack(fill="x", padx=40)
        pw1 = ctk.CTkEntry(fr, show="●", placeholder_text="Mínimo 8 caracteres",
                           height=44, font=ctk.CTkFont("Segoe UI", 13),
                           fg_color=C_SURFACE2, border_color=C_BORDER, border_width=1)
        pw1.pack(fill="x", padx=40, pady=(4, 12))

        ctk.CTkLabel(fr, text="CONFIRMAR SENHA", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=C_MUTED, anchor="w").pack(fill="x", padx=40)
        pw2 = ctk.CTkEntry(fr, show="●", placeholder_text="Repita a senha",
                           height=44, font=ctk.CTkFont("Segoe UI", 13),
                           fg_color=C_SURFACE2, border_color=C_BORDER, border_width=1)
        pw2.pack(fill="x", padx=40, pady=(4, 20))

        # Indicador de força
        strength_var = tk.StringVar(value="")
        strength_lbl = ctk.CTkLabel(fr, textvariable=strength_var,
                                    font=ctk.CTkFont("Segoe UI", 11),
                                    text_color=C_MUTED)
        strength_lbl.pack(pady=(0, 8))

        def on_key(*_):
            p = pw1.get()
            score, label, color = _password_strength(p)
            strength_var.set(f"Força: {label}")
            strength_lbl.configure(text_color=color)

        pw1.bind("<KeyRelease>", on_key)

        err_var = tk.StringVar(value="")
        ctk.CTkLabel(fr, textvariable=err_var, text_color=C_DANGER,
                     font=ctk.CTkFont("Segoe UI", 11)).pack()

        def do_create():
            p1, p2 = pw1.get(), pw2.get()
            if len(p1) < 8:
                err_var.set("❌  A senha deve ter no mínimo 8 caracteres.")
                return
            if p1 != p2:
                err_var.set("❌  As senhas não coincidem.")
                return
            self.auth.create_password(p1)
            self._password_cache = p1
            self._set_status("✔  Senha criada com sucesso.")
            self._show_main_screen()

        self._accent_btn(fr, "CRIAR COFRE", do_create)
        pw2.bind("<Return>", lambda _: do_create())

    # ════════════════════════════════════════════════════════════════════════════
    # TELA: Login
    # ════════════════════════════════════════════════════════════════════════════
    def _show_login_screen(self):
        self._clear_content()
        fr = self._content

        # Verifica lockout imediato
        locked, remaining = self.auth.is_locked()

        self._section_label(fr, "AUTENTICAÇÃO")

        ctk.CTkFrame(fr, height=20, fg_color="transparent").pack()

        # Ícone de cadeado
        ctk.CTkLabel(fr, text="🔒", font=ctk.CTkFont("Segoe UI", 52),
                     fg_color="transparent").pack()
        ctk.CTkFrame(fr, height=16, fg_color="transparent").pack()

        ctk.CTkLabel(fr, text="SENHA MESTRA", font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=C_MUTED, anchor="w").pack(fill="x", padx=40)
        pw_entry = ctk.CTkEntry(fr, show="●", placeholder_text="Digite sua senha",
                                height=48, font=ctk.CTkFont("Segoe UI", 14),
                                fg_color=C_SURFACE2, border_color=C_BORDER, border_width=1)
        pw_entry.pack(fill="x", padx=40, pady=(4, 16))

        err_var = tk.StringVar(value="")
        err_lbl = ctk.CTkLabel(fr, textvariable=err_var, text_color=C_DANGER,
                               font=ctk.CTkFont("Segoe UI", 11), wraplength=400)
        err_lbl.pack(pady=(0, 8))

        btn = self._accent_btn(fr, "DESBLOQUEAR", None)

        if locked:
            pw_entry.configure(state="disabled")
            btn.configure(state="disabled")
            self._start_lockout_countdown(err_var, pw_entry, btn, remaining)

        def do_login():
            pw = pw_entry.get()
            if not pw:
                err_var.set("⚠  Digite a senha.")
                return
            try:
                self.auth.verify_password(pw)
                self._password_cache = pw
                err_var.set("")
                self._set_status("✔  Autenticado.")
                self._show_main_screen()
            except AuthLockedError as e:
                pw_entry.configure(state="disabled")
                btn.configure(state="disabled")
                err_var.set(f"🔴  {e}")
                self._start_lockout_countdown(err_var, pw_entry, btn, e.seconds_remaining)
            except AuthWrongPasswordError as e:
                err_var.set(f"❌  {e}")
                pw_entry.delete(0, "end")

        btn.configure(command=do_login)
        pw_entry.bind("<Return>", lambda _: do_login())
        pw_entry.focus()

    def _start_lockout_countdown(self, err_var, pw_entry, btn, seconds):
        def tick(remaining):
            if remaining <= 0:
                err_var.set("")
                pw_entry.configure(state="normal")
                btn.configure(state="normal")
                return
            m, s = divmod(remaining, 60)
            err_var.set(f"🔴  Bloqueado por {m:02d}:{s:02d}")
            self.after(1000, tick, remaining - 1)
        tick(seconds)

    # ════════════════════════════════════════════════════════════════════════════
    # TELA: Principal (cofre desbloqueado)
    # ════════════════════════════════════════════════════════════════════════════
    def _show_main_screen(self):
        self._clear_content()
        fr = self._content

        # Estado do cofre
        stealth = self._get_stealth()
        is_hidden = stealth.is_hidden() if stealth else False

        self._section_label(fr, "PAINEL DO COFRE")

        # Card de status
        status_card = ctk.CTkFrame(fr, fg_color=C_SURFACE2,
                                   corner_radius=12, border_width=1,
                                   border_color=C_BORDER)
        status_card.pack(fill="x", padx=40, pady=(8, 20))

        icon = "🔴" if not is_hidden else "🟢"
        estado = "EXPOSTA" if not is_hidden else "PROTEGIDA"
        cor = C_DANGER if not is_hidden else C_SUCCESS

        ctk.CTkLabel(status_card, text=f"{icon}  Pasta: {estado}",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=cor).pack(pady=12)

        if is_hidden and stealth:
            loc = stealth.get_location()
            if loc:
                ctk.CTkLabel(status_card, text=f"Local secreto: ...{str(loc)[-40:]}",
                             font=ctk.CTkFont("Courier New", 9),
                             text_color=C_MUTED).pack(pady=(0, 8))

        ctk.CTkFrame(fr, height=8, fg_color="transparent").pack()

        # ── Botão principal: Trancar / Destrancar ─────────────────────────────
        if not is_hidden:
            # Selecionar e trancar
            self._folder_path = tk.StringVar(value="")

            ctk.CTkLabel(fr, text="PASTA PARA PROTEGER",
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=C_MUTED, anchor="w").pack(fill="x", padx=40)

            path_fr = ctk.CTkFrame(fr, fg_color="transparent")
            path_fr.pack(fill="x", padx=40, pady=(4, 16))

            path_entry = ctk.CTkEntry(path_fr, textvariable=self._folder_path,
                                      height=40, font=ctk.CTkFont("Segoe UI", 11),
                                      fg_color=C_SURFACE2, border_color=C_BORDER,
                                      border_width=1, placeholder_text="Nenhuma pasta selecionada")
            path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            ctk.CTkButton(path_fr, text="📁", width=44, height=40,
                          fg_color=C_SURFACE2, hover_color=C_BORDER,
                          command=self._browse_folder).pack(side="left")

            self._accent_btn(fr, "🔒  TRANCAR & ESCONDER", self._lock_vault,
                             color=C_DANGER)
        else:
            # Destrancar
            self._accent_btn(fr, "🔓  REVELAR & DESCRIPTOGRAFAR", self._unlock_vault,
                             color=C_ACCENT)

        # ── Separador ─────────────────────────────────────────────────────────
        ctk.CTkFrame(fr, height=1, fg_color=C_BORDER).pack(fill="x", padx=40, pady=20)

        # ── Ações secundárias ─────────────────────────────────────────────────
        sec_fr = ctk.CTkFrame(fr, fg_color="transparent")
        sec_fr.pack(fill="x", padx=40)

        self._secondary_btn(sec_fr, "⚙  Configurações", self._show_settings_screen)
        self._secondary_btn(sec_fr, "🔑  Trocar Senha",  self._show_change_password_screen)
        self._secondary_btn(sec_fr, "🚨  Botão de Pânico", self._panic_button)
        self._secondary_btn(sec_fr, "🔒  Bloquear App", self._lock_app)

        # Progresso (oculto até precisar)
        self._progress_var = tk.DoubleVar(value=0)
        self._progress_lbl = tk.StringVar(value="")
        self._progress_bar = ctk.CTkProgressBar(fr, variable=self._progress_var,
                                                 fg_color=C_SURFACE2,
                                                 progress_color=C_ACCENT)
        self._progress_info = ctk.CTkLabel(fr, textvariable=self._progress_lbl,
                                           font=ctk.CTkFont("Segoe UI", 10),
                                           text_color=C_MUTED)

    # ─── Ações do cofre ───────────────────────────────────────────────────────
    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta para proteger")
        if folder:
            self._folder_path.set(folder)

    def _lock_vault(self):
        folder_str = self._folder_path.get().strip()
        if not folder_str:
            messagebox.showwarning("X-Vault", "Selecione uma pasta primeiro.")
            return
        folder = Path(folder_str)
        if not folder.exists():
            messagebox.showerror("X-Vault", "Pasta não encontrada.")
            return

        confirm = messagebox.askyesno(
            "Confirmar",
            f"Criptografar e esconder:\n{folder}\n\nEsta pasta será MOVIDA e criptografada.\nContinuar?"
        )
        if not confirm:
            return

        self._run_in_thread(self._do_lock, folder)

    def _do_lock(self, source_folder: Path):
        try:
            pw   = self._password_cache
            key  = self.auth.derive_key(pw)
            crypto  = CryptoEngine(key)
            stealth = self._get_stealth()

            import tempfile
            tmp_enc = Path(tempfile.mkdtemp(prefix="xvlt_enc_"))

            # 1. Criptografa
            self._update_progress(0, "Criptografando arquivos...")
            def prog(cur, tot, name):
                pct = cur / tot if tot else 0
                self._update_progress(pct, f"Cifrando: {name}")

            crypto.encrypt_folder(source_folder, tmp_enc, progress_cb=prog)

            # 2. Esconde
            self._update_progress(0.95, "Escondendo pasta...")
            stealth.hide(tmp_enc)

            # 3. Remove original
            import shutil
            shutil.rmtree(str(source_folder), ignore_errors=True)

            self._update_progress(1.0, "Concluído!")
            self.after(500, lambda: self._set_status("✔  Pasta trancada e escondida."))
            self.after(600, self._show_main_screen)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao trancar:\n{e}"))
            self.after(0, self._show_main_screen)

    def _unlock_vault(self):
        folder = filedialog.askdirectory(title="Onde restaurar a pasta?")
        if not folder:
            return
        dest = Path(folder)
        self._run_in_thread(self._do_unlock, dest)

    def _do_unlock(self, destination: Path):
        try:
            pw      = self._password_cache
            key     = self.auth.derive_key(pw)
            crypto  = CryptoEngine(key)
            stealth = self._get_stealth()

            if not stealth.is_hidden():
                self.after(0, lambda: messagebox.showinfo("X-Vault", "Nenhuma pasta escondida encontrada."))
                return

            import tempfile
            tmp_dec = destination / "X-Vault_Restaurado"
            tmp_enc = stealth.get_location()

            # 1. Descriptografa
            self._update_progress(0, "Descriptografando...")
            def prog(cur, tot, name):
                pct = cur / tot if tot else 0
                self._update_progress(pct, f"Decifrando: {name}")

            crypto.decrypt_folder(tmp_enc, tmp_dec, progress_cb=prog)

            # 2. Remove do esconderijo
            self._update_progress(0.95, "Removendo do esconderijo...")
            import shutil
            shutil.rmtree(str(tmp_enc), ignore_errors=True)
            loc_file = Path(os.getenv("APPDATA")) / "XVault" / ".loc"
            if loc_file.exists():
                loc_file.unlink()

            self._update_progress(1.0, "Concluído!")
            self.after(500, lambda: messagebox.showinfo(
                "X-Vault", f"✔  Pasta restaurada em:\n{tmp_dec}"
            ))
            self.after(600, self._show_main_screen)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao destrancar:\n{e}"))
            self.after(0, self._show_main_screen)

    # ─── Botão de pânico ──────────────────────────────────────────────────────
    def _panic_button(self):
        confirm = messagebox.askyesno(
            "⚠ BOTÃO DE PÂNICO",
            "ATENÇÃO: Esta ação irá:\n\n"
            "• Apagar a senha e chave de autenticação\n"
            "• Tornar a pasta IRRECUPERÁVEL sem a senha\n\n"
            "Use apenas em emergência!\nTem certeza?",
            icon="warning"
        )
        if confirm:
            self.auth.reset_password()
            self._password_cache = None
            self._set_status("⚠  Dados de autenticação apagados.")
            messagebox.showinfo("X-Vault", "Botão de pânico ativado.\nO app será reiniciado.")
            self._show_initial_screen()

    # ════════════════════════════════════════════════════════════════════════════
    # TELA: Configurações
    # ════════════════════════════════════════════════════════════════════════════
    def _show_settings_screen(self):
        self._clear_content()
        fr = self._content

        self._section_label(fr, "CONFIGURAÇÕES")

        s = self.settings

        # Auto-lock
        ctk.CTkLabel(fr, text="BLOQUEIO AUTOMÁTICO (minutos)",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=C_MUTED, anchor="w").pack(fill="x", padx=40, pady=(12, 4))
        lock_var = tk.StringVar(value=str(s.get("auto_lock_minutes", 5)))
        lock_entry = ctk.CTkEntry(fr, textvariable=lock_var, height=40,
                                  fg_color=C_SURFACE2, border_color=C_BORDER, border_width=1)
        lock_entry.pack(fill="x", padx=40, pady=(0, 12))

        # Pânico automático
        panic_var = tk.BooleanVar(value=s.get("panic_on_wrong_attempts", True))
        ctk.CTkSwitch(fr, text="Pânico após tentativas erradas",
                      variable=panic_var,
                      progress_color=C_ACCENT,
                      font=ctk.CTkFont("Segoe UI", 12)).pack(anchor="w", padx=40, pady=8)

        # Ícone na bandeja
        tray_var = tk.BooleanVar(value=s.get("show_tray_icon", True))
        ctk.CTkSwitch(fr, text="Mostrar ícone na bandeja do sistema",
                      variable=tray_var,
                      progress_color=C_ACCENT,
                      font=ctk.CTkFont("Segoe UI", 12)).pack(anchor="w", padx=40, pady=8)

        ctk.CTkFrame(fr, height=16, fg_color="transparent").pack()

        def save_settings():
            try:
                mins = int(lock_var.get())
                if mins < 1: mins = 1
            except:
                mins = 5
            s.set("auto_lock_minutes", mins)
            s.set("panic_on_wrong_attempts", panic_var.get())
            s.set("show_tray_icon", tray_var.get())
            self._set_status("✔  Configurações salvas.")
            self._show_main_screen()

        self._accent_btn(fr, "SALVAR", save_settings)
        self._secondary_btn_inline(fr, "← Voltar", self._show_main_screen)

    # ════════════════════════════════════════════════════════════════════════════
    # TELA: Trocar Senha
    # ════════════════════════════════════════════════════════════════════════════
    def _show_change_password_screen(self):
        self._clear_content()
        fr = self._content
        self._section_label(fr, "TROCAR SENHA")

        ctk.CTkFrame(fr, height=12, fg_color="transparent").pack()

        for lbl, key in [
            ("SENHA ATUAL", "old"),
            ("NOVA SENHA",  "new"),
            ("CONFIRMAR",   "confirm"),
        ]:
            ctk.CTkLabel(fr, text=lbl, font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=C_MUTED, anchor="w").pack(fill="x", padx=40)
            e = ctk.CTkEntry(fr, show="●", height=44, fg_color=C_SURFACE2,
                             border_color=C_BORDER, border_width=1,
                             font=ctk.CTkFont("Segoe UI", 13))
            e.pack(fill="x", padx=40, pady=(4, 12))
            setattr(self, f"_cp_{key}", e)

        err_var = tk.StringVar()
        ctk.CTkLabel(fr, textvariable=err_var, text_color=C_DANGER,
                     font=ctk.CTkFont("Segoe UI", 11)).pack()

        def do_change():
            old = self._cp_old.get()
            new = self._cp_new.get()
            conf = self._cp_confirm.get()
            if len(new) < 8:
                err_var.set("❌  Nova senha: mínimo 8 caracteres.")
                return
            if new != conf:
                err_var.set("❌  Senhas não coincidem.")
                return
            if self.auth.change_password(old, new):
                self._password_cache = new
                self._set_status("✔  Senha alterada.")
                self._show_main_screen()
            else:
                err_var.set("❌  Senha atual incorreta.")

        self._accent_btn(fr, "ALTERAR SENHA", do_change)
        self._secondary_btn_inline(fr, "← Voltar", self._show_main_screen)

    # ─── Bloquear app ─────────────────────────────────────────────────────────
    def _lock_app(self):
        self._password_cache = None
        self._show_login_screen()

    # ─── Helpers de UI ────────────────────────────────────────────────────────
    def _section_label(self, parent, text: str):
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C_ACCENT, anchor="w").pack(
                         fill="x", padx=40, pady=(20, 4))

    def _info_label(self, parent, text: str):
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C_MUTED, anchor="w",
                     justify="left", wraplength=420).pack(fill="x", padx=40)

    def _accent_btn(self, parent, text, cmd, color=None) -> ctk.CTkButton:
        color = color or C_ACCENT
        btn = ctk.CTkButton(
            parent, text=text, command=cmd,
            height=48, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=color, hover_color=_darken(color),
            text_color="#000000" if color == C_ACCENT else C_TEXT
        )
        btn.pack(fill="x", padx=40, pady=(8, 4))
        return btn

    def _secondary_btn(self, parent, text, cmd):
        ctk.CTkButton(
            parent, text=text, command=cmd,
            height=38, corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=C_SURFACE2, hover_color=C_BORDER,
            text_color=C_TEXT, border_width=1, border_color=C_BORDER
        ).pack(fill="x", pady=4)

    def _secondary_btn_inline(self, parent, text, cmd):
        ctk.CTkButton(
            parent, text=text, command=cmd,
            height=36, width=140,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent", hover_color=C_SURFACE2,
            text_color=C_MUTED
        ).pack(pady=8)

    def _set_status(self, msg: str):
        self._status_var.set(f"  {msg}")

    def _update_progress(self, pct: float, label: str = ""):
        self._progress_var.set(pct)
        self._progress_lbl.set(label)
        try:
            self._progress_bar.pack(fill="x", padx=40, pady=(8, 0))
            self._progress_info.pack()
        except:
            pass
        self.update_idletasks()

    # ─── Thread helper ────────────────────────────────────────────────────────
    def _run_in_thread(self, fn, *args):
        t = threading.Thread(target=fn, args=args, daemon=True)
        t.start()

    # ─── Stealth helper ───────────────────────────────────────────────────────
    def _get_stealth(self) -> StealthModule | None:
        if not self._password_cache:
            return None
        key = self.auth.derive_key(self._password_cache)
        return StealthModule(key)

    # ─── Fechar janela ────────────────────────────────────────────────────────
    def _on_close(self):
        self._password_cache = None
        self.destroy()


# ─── Helpers globais ─────────────────────────────────────────────────────────
def _password_strength(pw: str) -> tuple[int, str, str]:
    score = 0
    if len(pw) >= 8:  score += 1
    if len(pw) >= 12: score += 1
    if any(c.isdigit() for c in pw):    score += 1
    if any(c.isupper() for c in pw):    score += 1
    if any(c in "!@#$%^&*_-+" for c in pw): score += 1

    if score <= 2: return score, "Fraca",  C_DANGER
    if score <= 3: return score, "Média",  C_WARNING
    return score, "Forte", C_SUCCESS

def _darken(hex_color: str, factor: float = 0.8) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = XVaultApp()
    app.mainloop()
