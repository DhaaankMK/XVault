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

## ⚠️ AVISO DE RESPONSABILIDADE (DISCLAIMER)

> 🛑 **LEIA COM ATENÇÃO:** O **XVault** é estritamente uma ferramenta de software para estudo e uso pessoal de criptografia e ocultação de diretórios. O uso deste aplicativo é de sua inteira e exclusiva responsabilidade.
>
> **NÃO NOS RESPONSABILIZAMOS POR:**
> * 🔑 **Senhas Esquecidas:** A criptografia utilizada (AES-256) é de nível militar e irreversível sem a chave correta. Se você esquecer a senha que definiu, **NÃO HÁ NENHUMA FORMA** de recuperar seus arquivos. Não existe botão de "esqueci minha senha".
> * 📁 **Arquivos Perdidos ou Corrompidos:** Falhas no sistema operacional, encerramento forçado do app durante o processo ou exclusão acidental da pasta camuflada podem resultar em perda permanente de dados.
> * 💻 **Danificações no Sistema:** O uso incorreto de privilégios de Administrador ou modificação manual dos arquivos de configuração do app são por sua conta e risco.
>
> O desenvolvedor se isenta de qualquer responsabilidade por danos diretos, indiretos, perdas de dados ou qualquer outro prejuízo decorrente do uso ou da incapacidade de usar esta ferramenta. **Faça sempre backup dos seus arquivos importantes antes de testar o software.**

---

## 🚀 Requisitos

- Windows 10/11 (64-bit)
- Python 3.11+ (para desenvolvimento)
- `customtkinter >= 5.2.2`
- `cryptography >= 41.0.0`
