# ◈ X-Vault — Cofre de Arquivos Criptografado

Software de proteção de dados com criptografia AES-256-GCM real,  
modo stealth profundo e interface dark profissional.

---

## 📂 Estrutura do Projeto

```
XVault/
├── src/
│   ├── main.py              ← Interface principal (CustomTkinter)
│   ├── crypto_engine.py     ← Criptografia AES-256-GCM por arquivo
│   ├── stealth_module.py    ← Ocultação profunda no sistema Windows
│   ├── auth_manager.py      ← Senha + PBKDF2 + anti-brute-force
│   └── settings_manager.py ← Configurações persistentes
├── assets/
│   └── icon.ico             ← Ícone do app (adicione o seu)
├── requirements.txt
├── build.spec               ← PyInstaller (gera .exe com UAC)
└── run_admin.bat            ← Launcher com elevação automática
```

---

## ⚙️ Instalação

### 1. Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 2. Executar (desenvolvimento)
```bash
# Com .bat (recomendado — eleva automaticamente):
run_admin.bat

# Ou diretamente:
python src/main.py
```

### 3. Gerar .exe (distribuição)
```bash
pip install pyinstaller
pyinstaller build.spec
# Resultado: dist/XVault.exe  (com escudo UAC no ícone)
```

---

## 🛡️ Segurança — Como Funciona

### Autenticação
- Senha derivada com **PBKDF2-SHA256** com 200.000 iterações + salt aleatório de 32 bytes
- Comparação segura via `hmac.compare_digest` (proteção contra timing attacks)
- **Anti-brute-force**: 3 tentativas → bloqueio de 10 minutos
- **Botão de Pânico**: apaga dados de autenticação → pasta fica irrecuperável sem a senha

### Criptografia
- **AES-256-GCM** arquivo por arquivo (via `cryptography` — não é zip/rar)
- Cada arquivo recebe um **nonce único de 12 bytes**
- Autenticação integrada (GCM) — qualquer adulteração é detectada
- Nomes dos arquivos são embaralhados com hash SHA-1
- Mapa nome→arquivo criptografado está também criptografado (`.xmap`)

### Modo Stealth
- Pasta movida para dentro de `%LOCALAPPDATA%\Microsoft\Windows\Caches` (ou similar)
- Renomeada para um CLSID de sistema falso (ex: `{6DFD7C5C-2451-11d3-...}`)
- Atributos **HIDDEN + SYSTEM** aplicados via `SetFileAttributesW`
- Localização guardada em arquivo `.loc` **criptografado com a chave da senha**
- Sem a senha → não dá pra saber onde está nem o que é

---

## ⚠️ Avisos Importantes

1. **NÃO esqueça sua senha.** Sem ela a pasta é permanentemente irrecuperável.
2. Execute sempre como **Administrador** para garantir acesso total às APIs do Windows.
3. Faça backup da pasta **antes** de trancar pela primeira vez, até ter certeza que sabe usar.
4. O `.exe` gerado pelo PyInstaller contém tudo — Python, bibliotecas e código. É portátil.

---

## 🚀 Requisitos

- Windows 10/11 (64-bit)
- Python 3.11+ (para desenvolvimento)
- `customtkinter >= 5.2.2`
- `cryptography >= 41.0.0`
