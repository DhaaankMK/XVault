"""
X-Vault :: stealth_module.py
Esconde a pasta privada profundamente no sistema:
  - Renomeia para um CLSID/GUID de sistema falso
  - Move para dentro de AppData\\Local\\Microsoft\\Windows
  - Aplica atributos HIDDEN + SYSTEM via ctypes
  - Registra o caminho secreto de forma criptografada
"""

import os
import ctypes
import shutil
import json
import random
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ─── CLSIDs de sistema que parecem legítimos ──────────────────────────────────
_FAKE_CLSIDS = [
    "{6DFD7C5C-2451-11d3-A299-00C04F8EF6AF}",
    "{2227A280-3AEA-1069-A2DE-08002B30309D}",
    "{450D8FBA-AD25-11D0-98A8-0800361B1103}",
    "{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
    "{645FF040-5081-101B-9F08-00AA002F954E}",
    "{7007ACC7-3202-11D1-AAD2-00805FC1270E}",
    "{992CFFA0-F557-101A-88EC-00DD010CCC48}",
    "{D20EA4E1-3957-11d2-A40B-0C5020524152}",
    "{D20EA4E1-3957-11d2-A40B-0C5020524153}",
    "{B4FB3F98-C1EA-428d-A78A-D1F5659CBA93}",
]

# Caminhos de esconderijo dentro do sistema
_HIDING_SPOTS = [
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Caches",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "INetCache",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "CLR_v4.0",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "WER",
    Path(os.getenv("APPDATA", ""))      / "Microsoft" / "Windows" / "Recent" / "AutomaticDestinations",
    Path(os.getenv("APPDATA", ""))      / "Microsoft" / "Windows" / "Recent" / "CustomDestinations",
    Path(os.getenv("LOCALAPPDATA", "")) / "Packages",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "OneDrive" / "logs",
]

# Arquivo que guarda onde a pasta foi escondida (criptografado)
_CONFIG_DIR    = Path(os.getenv("APPDATA", "")) / "XVault"
_LOCATION_FILE = _CONFIG_DIR / ".loc"


class StealthModule:
    """Esconde e recupera a pasta privada do usuário."""

    def __init__(self, master_key: bytes):
        """master_key: 32 bytes derivados da senha pelo AuthManager."""
        self._aesgcm = AESGCM(master_key)
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Esconder pasta ───────────────────────────────────────────────────────
    def hide(self, source_folder: Path) -> Path:
        """
        Move source_folder para um esconderijo do sistema.
        Retorna o caminho secreto onde foi guardada.
        """
        if not source_folder.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {source_folder}")

        # Escolhe CLSID e localização aleatórios
        clsid    = random.choice(_FAKE_CLSIDS)
        spot     = self._choose_spot()
        dst_path = spot / clsid

        # Garante que o destino não existe
        if dst_path.exists():
            clsid    = self._unique_clsid(spot)
            dst_path = spot / clsid

        spot.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_folder), str(dst_path))

        # Aplica atributos ocultos + sistema
        self._set_hidden_system(dst_path)

        # Salva localização criptografada
        self._save_location(dst_path)

        return dst_path

    # ─── Restaurar pasta ──────────────────────────────────────────────────────
    def unhide(self, destination_folder: Path) -> bool:
        """
        Move a pasta do esconderijo de volta para destination_folder.
        Retorna True se bem-sucedido.
        """
        secret_path = self.get_location()
        if not secret_path or not secret_path.exists():
            return False

        destination_folder.parent.mkdir(parents=True, exist_ok=True)

        # Remove atributos ocultos antes de mover
        self._remove_hidden_system(secret_path)
        shutil.move(str(secret_path), str(destination_folder))

        # Apaga registro de localização
        if _LOCATION_FILE.exists():
            _LOCATION_FILE.unlink()

        return True

    # ─── Localização ─────────────────────────────────────────────────────────
    def get_location(self) -> Path | None:
        """Retorna o caminho secreto atual, ou None se não houver."""
        if not _LOCATION_FILE.exists():
            return None
        try:
            raw   = _LOCATION_FILE.read_bytes()
            nonce = raw[:12]
            cdata = raw[12:]
            data  = self._aesgcm.decrypt(nonce, cdata, None)
            return Path(json.loads(data.decode())["path"])
        except Exception:
            return None

    def is_hidden(self) -> bool:
        loc = self.get_location()
        return loc is not None and loc.exists()

    def _save_location(self, path: Path):
        import os as _os
        nonce = _os.urandom(12)
        data  = json.dumps({"path": str(path)}).encode()
        cdata = self._aesgcm.encrypt(nonce, data, None)
        _LOCATION_FILE.write_bytes(nonce + cdata)

    # ─── Atributos do Windows ─────────────────────────────────────────────────
    @staticmethod
    def _set_hidden_system(path: Path):
        """FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM"""
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x02
            FILE_ATTRIBUTE_SYSTEM = 0x04
            ctypes.windll.kernel32.SetFileAttributesW(
                str(path),
                FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
            )
        except Exception:
            pass  # Não-Windows ou sem permissão — silencioso

    @staticmethod
    def _remove_hidden_system(path: Path):
        try:
            FILE_ATTRIBUTE_NORMAL = 0x80
            ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_NORMAL)
        except Exception:
            pass

    # ─── Helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _choose_spot() -> Path:
        """Escolhe aleatoriamente um esconderijo que exista ou possa ser criado."""
        random.shuffle(_HIDING_SPOTS)
        for spot in _HIDING_SPOTS:
            try:
                spot.mkdir(parents=True, exist_ok=True)
                # Testa se consegue escrever lá
                test = spot / ".xtest"
                test.touch()
                test.unlink()
                return spot
            except Exception:
                continue
        # Fallback: AppData raiz
        return _CONFIG_DIR / "data"

    @staticmethod
    def _unique_clsid(spot: Path) -> str:
        """Gera um CLSID que ainda não existe naquele spot."""
        for clsid in _FAKE_CLSIDS:
            if not (spot / clsid).exists():
                return clsid
        # Gera um UUID-like se todos estiverem ocupados
        import uuid
        return "{" + str(uuid.uuid4()).upper() + "}"


# ─── Utilitário: verificar admin ──────────────────────────────────────────────
def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def relaunch_as_admin(script_path: str):
    """Re-executa o script atual como administrador via UAC."""
    import sys
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script_path}"', None, 1
    )
