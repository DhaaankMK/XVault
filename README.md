# 🔒 X-Vault | Advanced Folder Stealth & Encryption

![Status](https://img.shields.io/badge/Status-Development-orange)
![Security](https://img.shields.io/badge/Security-AES--256-red)
![OS](https://img.shields.io/badge/OS-Windows-blue)

**X-Vault** é um software de segurança modular desenvolvido em Python, focado em ocultação profunda e criptografia de arquivos. Ele transforma diretórios comuns em cofres invisíveis dentro do ecossistema do Windows.

---

## 🛡️ Funcionalidades Focadas em Proteção

- **Criptografia Real:** Utiliza a biblioteca `cryptography` (AES-256) para tornar os arquivos ilegíveis sem a chave correta.
- **Deep Stealth (Ocultação Profunda):** - Move a pasta para diretórios do sistema (ex: `%AppData%`).
  - Mascara a pasta usando **CLSID/GUID** (fazendo-a parecer um ícone do Painel de Controle).
  - Atributos de sistema ocultos (`+h +s`).
- **Execução com Privilégios:** O app solicita automaticamente permissão de **Administrador** para manipular pastas restritas.
- **Interface Moderna:** Desenvolvido com `CustomTkinter` para um visual Dark/Moderno.
- **Gestão de Senhas Segura:** Armazenamento de senhas via Hash (SHA-256), garantindo que nem o desenvolvedor saiba a senha pura.

## 📂 Estrutura do Aplicativo

O projeto é dividido de forma modular para maior segurança e organização:

* `main.py`: Interface gráfica (GUI) e controle principal.
* `crypto_engine.py`: Motor de criptografia e descriptografia de arquivos.
* `stealth_module.py`: Lógica de movimentação, renomeação e ocultação no Windows.
* `auth_manager.py`: Sistema de login, validação de hash e troca de senha.

## 🚀 Como Utilizar

1. **Requisitos:** Tenha o Python 3.10+ instalado.
2. **Dependências:**
   ```bash
   pip install cryptography customtkinter
