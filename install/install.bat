@echo on

:: Baixar Python 3.12 (substitua este comentário por instruções específicas de instalação, se necessário)

:: Verificar a instalação do Python 3.12
python3.12 --version

:: Criar e ativar o ambiente virtual
python3.12 -m venv .venv
call .venv\Scripts\activate

:: Atualizar pip e instalar dependências
python -m pip install --upgrade pip
::pip install pipx
::pipx ensurepath

poetry env activate
pip install poetry
::pip install -r requirements.txt

:: poetry install

:: Inicia o pre-commit
pre-commit install

echo Instalação concluída com sucesso!
pause
