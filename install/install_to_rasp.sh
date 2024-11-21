#!/bin/bash

# Instalar Dependências Necessárias
sudo apt update && sudo apt upgrade -y
sudo apt install -y wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev

# Baixar o Código-Fonte do Python 3.12
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz

## Descompacte o arquivo:
tar -xvzf Python-3.12.0.tgz
cd Python-3.12.0

# Compilar e Instalar
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall

# Verificar a Instalação
python3.12 --version

# Criar e ativar o ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# Atualizar pip e instalar dependências
pip install --upgrade pip
sudo apt install pipx
pipx ensurepath
pipx install poetry

poetry install
pip install -r requirements.txt

# Inicia o pre-commit
pre-commit install

echo "Instalação concluída com sucesso!"
