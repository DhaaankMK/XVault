"""
X-Vault :: auth_manager.py
Gerencia autenticação com hash SHA-256 + salt, anti-brute-force e lockout.
"""

import hashlib
import hmac
import os
import json
import time
from pathlib import Path

# ─── Constantes ──────────────────────────────────────────────────────────────
MAX_ATTEMPTS     = 3          # Tentativas antes do lockout
LOCKOUT_SECONDS  = 600        # 10 minutos de bloqueio
CONFIG_DIR       = Path(os.getenv("APPDATA")) / "XVault"
AUTH_FILE        = CONFIG_DIR / ".auth"


class AuthManager:
    """Responsável por criar, verificar e proteger a senha mestra."""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    # ─── Estado persistente ───────────────────────────────────────────────────
    def _load_state(self) -> dict:
        if AUTH_FILE.exists():
            try:
                with open(AUTH_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "hash": None,
            "salt": None,
            "attempts": 0,
            "lockout_until": 0,
        }

    def _save_state(self):
        with open(AUTH_FILE, "w") as f:
            json.dump(self._state, f)

    # ─── Criação de senha ─────────────────────────────────────────────────────
    def has_password(self) -> bool:
        return self._state.get("hash") is not None

    def create_password(self, password: str) -> bool:
        """Cria e armazena hash+salt da senha. Retorna False se já existe."""
        if self.has_password():
            return False
        salt = os.urandom(32).hex()
        pw_hash = self._hash_password(password, salt)
        self._state["hash"] = pw_hash
        self._state["salt"] = salt
        self._state["attempts"] = 0
        self._state["lockout_until"] = 0
        self._save_state()
        return True

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Troca a senha após verificar a antiga."""
        if not self.verify_password(old_password):
            return False
        salt = os.urandom(32).hex()
        self._state["hash"] = self._hash_password(new_password, salt)
        self._state["salt"] = salt
        self._state["attempts"] = 0
        self._save_state()
        return True

    def reset_password(self):
        """Apaga completamente os dados de autenticação (botão de pânico)."""
        self._state = {
            "hash": None, "salt": None,
            "attempts": 0, "lockout_until": 0,
        }
        self._save_state()

    # ─── Verificação ──────────────────────────────────────────────────────────
    def verify_password(self, password: str) -> bool:
        """
        Verifica a senha. Aplica lockout se exceder MAX_ATTEMPTS.
        Lança AuthLockedError se estiver bloqueado.
        """
        self._check_lockout()

        salt   = self._state["salt"]
        stored = self._state["hash"]
        pw_hash = self._hash_password(password, salt)

        # Comparação segura contra timing attacks
        if hmac.compare_digest(pw_hash, stored):
            self._state["attempts"] = 0
            self._save_state()
            return True

        # Senha errada — incrementa tentativas
        self._state["attempts"] += 1
        if self._state["attempts"] >= MAX_ATTEMPTS:
            self._state["lockout_until"] = time.time() + LOCKOUT_SECONDS
            self._save_state()
            raise AuthLockedError(LOCKOUT_SECONDS)

        self._save_state()
        remaining = MAX_ATTEMPTS - self._state["attempts"]
        raise AuthWrongPasswordError(remaining)

    # ─── Lockout ─────────────────────────────────────────────────────────────
    def _check_lockout(self):
        until = self._state.get("lockout_until", 0)
        if until and time.time() < until:
            remaining = int(until - time.time())
            raise AuthLockedError(remaining)
        # Lockout expirou — resetar contagem
        if until and time.time() >= until:
            self._state["attempts"] = 0
            self._state["lockout_until"] = 0
            self._save_state()

    def is_locked(self) -> tuple[bool, int]:
        """Retorna (True, segundos_restantes) se bloqueado, senão (False, 0)."""
        until = self._state.get("lockout_until", 0)
        if until and time.time() < until:
            return True, int(until - time.time())
        return False, 0

    # ─── Hash ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """SHA-256 com salt + 200k iterações PBKDF2."""
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=200_000,
        )
        return dk.hex()

    def derive_key(self, password: str) -> bytes:
        """Deriva 32 bytes para usar como chave AES a partir da senha."""
        salt = self._state["salt"]
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=200_000,
            dklen=32,
        )
        return dk


# ─── Exceções customizadas ───────────────────────────────────────────────────
class AuthLockedError(Exception):
    def __init__(self, seconds_remaining: int):
        self.seconds_remaining = seconds_remaining
        minutes = seconds_remaining // 60
        super().__init__(f"App bloqueado. Tente novamente em {minutes} min.")

class AuthWrongPasswordError(Exception):
    def __init__(self, attempts_remaining: int):
        self.attempts_remaining = attempts_remaining
        super().__init__(f"Senha incorreta. {attempts_remaining} tentativa(s) restante(s).")
