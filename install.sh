#!/bin/bash

# Atualizar lista de pacotes e instalar dependências necessárias
sudo apt update
sudo apt install -y software-properties-common

# Adicionar o repositório de Python 3.9 e instalar o Python 3.9
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Verificar a instalação do Python 3.9
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
