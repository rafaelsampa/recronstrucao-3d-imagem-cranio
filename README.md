# Reconstrução 3D de crânio a partir de imagens CT

## Requisitos

- Python **3.12** (versões mais novas podem não ter o VTK/PyVista disponível)

## Setup

Na pasta do projeto, no PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> Se o PowerShell bloquear o `Activate.ps1`, rode antes:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Rodando os notebooks

### Opção 1: Jupyter Lab (navegador)

```powershell
jupyter lab
```

Abra os notebooks em `notebooks/` e execute na ordem (01 → 06).

### Opção 2: VS Code

1. Instale as extensões **Python** e **Jupyter** (Microsoft).
2. Abra a pasta do projeto no VS Code e abra um notebook em `notebooks/`.
3. Clique em **Selecionar Kernel** (canto superior direito) → **Python Environments** → **.venv**.
   - Se o `.venv` não aparecer, escolha **Enter interpreter path** e informe `.venv\Scripts\python.exe`.
4. Execute as células na ordem.

> Confira o kernel: ele deve ser o **.venv**, não um Python global do sistema.
