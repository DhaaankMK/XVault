"""
X-Vault :: crypto_engine.py
Criptografia AES-256-GCM real arquivo por arquivo.
Cada arquivo recebe um IV/nonce único. Sem a chave = lixo eletrônico.
"""

import os
import struct
from pathlib import Path
from typing import Callable

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ─── Constantes ──────────────────────────────────────────────────────────────
CHUNK_SIZE    = 64 * 1024        # 64 KB por chunk
NONCE_SIZE    = 12               # GCM standard nonce
TAG_SIZE      = 16               # GCM authentication tag
MAGIC_HEADER  = b"XVLT\x01"     # Assinatura do arquivo criptografado


class CryptoEngine:
    """
    Criptografa/descriptografa arquivos usando AES-256-GCM.

    Formato do arquivo .xvlt:
        [MAGIC 5B] [NONCE 12B] [DADOS_CIFRADOS + TAG 16B]
    """

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("A chave deve ter 32 bytes (AES-256).")
        self._aesgcm = AESGCM(key)

    # ─── Arquivo único ────────────────────────────────────────────────────────
    def encrypt_file(self, src: Path, dst: Path):
        """Criptografa src → dst.xvlt"""
        nonce = os.urandom(NONCE_SIZE)
        plaintext = src.read_bytes()
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)

        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(MAGIC_HEADER)
            f.write(nonce)
            f.write(ciphertext)

    def decrypt_file(self, src: Path, dst: Path):
        """Descriptografa src.xvlt → dst"""
        with open(src, "rb") as f:
            magic = f.read(len(MAGIC_HEADER))
            if magic != MAGIC_HEADER:
                raise ValueError(f"Arquivo inválido ou corrompido: {src.name}")
            nonce      = f.read(NONCE_SIZE)
            ciphertext = f.read()

        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(plaintext)

    # ─── Pasta inteira ────────────────────────────────────────────────────────
    def encrypt_folder(
        self,
        src_folder: Path,
        dst_folder: Path,
        progress_cb: Callable[[int, int, str], None] | None = None,
    ):
        """
        Criptografa toda a pasta src_folder → dst_folder.
        Estrutura de subpastas é preservada.
        Arquivos recebem extensão .xvlt e nomes originais são embaralhados.
        progress_cb(current, total, filename)
        """
        files = [p for p in src_folder.rglob("*") if p.is_file()]
        total = len(files)

        for i, src_file in enumerate(files, 1):
            rel = src_file.relative_to(src_folder)
            # Embaralha nome: usa índice + hash para dificultar reconhecimento
            safe_name = f"f{i:05d}_{_name_hash(str(rel))}.xvlt"
            dst_file  = dst_folder / _flatten_path(rel, safe_name)

            if progress_cb:
                progress_cb(i, total, src_file.name)

            self.encrypt_file(src_file, dst_file)

        # Salva mapa nome_original → nome_cifrado para poder restaurar
        self._save_name_map(files, src_folder, dst_folder)

    def decrypt_folder(
        self,
        src_folder: Path,
        dst_folder: Path,
        progress_cb: Callable[[int, int, str], None] | None = None,
    ):
        """Descriptografa toda a pasta, restaurando nomes e estrutura originais."""
        name_map = self._load_name_map(src_folder)
        files = [p for p in src_folder.rglob("*.xvlt") if p.is_file()]
        total = len(files)

        for i, src_file in enumerate(files, 1):
            rel_enc = str(src_file.relative_to(src_folder))
            original_rel = name_map.get(rel_enc)

            if original_rel:
                dst_file = dst_folder / original_rel
            else:
                # Fallback: remove .xvlt
                dst_file = dst_folder / src_file.relative_to(src_folder).with_suffix("")

            if progress_cb:
                progress_cb(i, total, dst_file.name)

            self.decrypt_file(src_file, dst_file)

    # ─── Mapa de nomes ────────────────────────────────────────────────────────
    def _save_name_map(self, files: list[Path], src_root: Path, dst_root: Path):
        """Salva mapa cifrado: {enc_rel: original_rel}"""
        import json
        mapping = {}
        for i, f in enumerate(files, 1):
            rel = f.relative_to(src_root)
            safe_name = f"f{i:05d}_{_name_hash(str(rel))}.xvlt"
            enc_rel   = str(_flatten_path(rel, safe_name))
            mapping[enc_rel] = str(rel)

        map_path = dst_root / ".xmap"
        # Criptografa o próprio mapa
        nonce = os.urandom(NONCE_SIZE)
        data  = json.dumps(mapping).encode()
        cdata = self._aesgcm.encrypt(nonce, data, None)
        map_path.write_bytes(MAGIC_HEADER + nonce + cdata)

    def _load_name_map(self, src_folder: Path) -> dict:
        import json
        map_path = src_folder / ".xmap"
        if not map_path.exists():
            return {}
        raw = map_path.read_bytes()
        nonce     = raw[len(MAGIC_HEADER): len(MAGIC_HEADER) + NONCE_SIZE]
        cdata     = raw[len(MAGIC_HEADER) + NONCE_SIZE:]
        data      = self._aesgcm.decrypt(nonce, cdata, None)
        return json.loads(data.decode())


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _name_hash(name: str) -> str:
    import hashlib
    return hashlib.sha1(name.encode()).hexdigest()[:8]

def _flatten_path(rel: Path, new_name: str) -> Path:
    """Mantém subpastas mas substitui o nome do arquivo."""
    parent = rel.parent
    return parent / new_name
