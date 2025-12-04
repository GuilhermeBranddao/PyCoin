#!/bin/bash

# ==========================================
# Configurações e Variáveis
# ==========================================
PYTHON_VERSION="3.12.0"
PYTHON_TAR="Python-$PYTHON_VERSION.tgz"
PYTHON_DIR="Python-$PYTHON_VERSION"
PYTHON_URL="https://www.python.org/ftp/python/$PYTHON_VERSION/$PYTHON_TAR"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arrays para o relatório
INSTALLED_SUCCESS=()
INSTALLED_FAIL=()
SKIPPED=()

echo -e "${BLUE}=== Iniciando Instalação para Raspberry Pi (Python $PYTHON_VERSION) ===${NC}"

# ==========================================
# Funções Auxiliares
# ==========================================

retry_command() {
    local n=1
    local max=3
    local delay=5
    while true; do
        "$@" && return 0
        if [[ $n -lt $max ]]; then
            ((n++))
            echo -e "${YELLOW}Comando falhou. Tentativa $n/$max em $delay s...${NC}"
            sleep $delay;
        else
            echo -e "${RED}O comando falhou após $n tentativas.${NC}"
            return 1
        fi
    done
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ==========================================
# 1. Instalação de Dependências de Build
# ==========================================
echo -e "\n${BLUE}[1/6] Atualizando sistema e dependências de compilação...${NC}"

if retry_command sudo apt update; then
    INSTALLED_SUCCESS+=("APT Update")
else
    INSTALLED_FAIL+=("APT Update")
fi

# Lista de libs necessárias para compilar o Python completo (SSL, SQlite, etc)
BUILD_DEPS="build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev"

echo "Instalando compiladores e bibliotecas..."
if retry_command sudo apt install -y $BUILD_DEPS; then
    INSTALLED_SUCCESS+=("Build Dependencies")
else
    INSTALLED_FAIL+=("Build Dependencies")
    echo -e "${RED}Erro crítico: Não é possível compilar sem dependências.${NC}"
    exit 1
fi

# ==========================================
# 2. Compilação do Python 3.12 (A parte pesada)
# ==========================================
echo -e "\n${BLUE}[2/6] Verificando Python $PYTHON_VERSION...${NC}"

if command_exists python3.12; then
    echo -e "${GREEN}✔ Python 3.12 já está instalado. Pulando compilação.${NC}"
    SKIPPED+=("Python 3.12 Compilation")
else
    echo -e "${YELLOW}⚠ ATENÇÃO: A compilação no Raspberry Pi pode levar de 20 a 60 minutos.${NC}"
    echo -e "☕ Vá pegar um café e não desligue o Pi..."

    # Download
    if [ ! -f "$PYTHON_TAR" ]; then
        echo "Baixando código-fonte..."
        retry_command wget "$PYTHON_URL"
    fi

    # Extração
    if [ ! -d "$PYTHON_DIR" ]; then
        echo "Extraindo arquivos..."
        tar -xzf "$PYTHON_TAR"
    fi

    cd "$PYTHON_DIR" || exit

    # Configuração
    echo "Configurando build (configure)..."
    # --enable-optimizations deixa o Python 10-20% mais rápido, mas a compilação demora mais
    ./configure --enable-optimizations

    # Compilação
    # nproc define quantos núcleos usar. No RPi 3/4/5 ajuda muito.
    CORES=$(nproc)
    echo "Compilando usando $CORES núcleos (make)..."
    if make -j"$CORES"; then
        echo "Instalando binários (altinstall)..."
        sudo make altinstall
        
        INSTALLED_SUCCESS+=("Python 3.12 Compiled")
        
        # Limpeza para economizar espaço no SD Card
        echo "Limpando arquivos de instalação..."
        cd ..
        sudo rm -rf "$PYTHON_DIR" "$PYTHON_TAR"
    else
        INSTALLED_FAIL+=("Python 3.12 Compilation")
        echo -e "${RED}Erro fatal na compilação.${NC}"
        exit 1
    fi
    
    # Volta para a raiz do script se tiver mudado de diretório
    cd ..
fi

# ==========================================
# 3. Poetry e Pipx
# ==========================================
echo -e "\n${BLUE}[3/6] Configurando Gerenciadores (Pipx/Poetry)...${NC}"

# Tenta instalar pipx via apt (mais seguro no Debian) ou via pip se falhar
if ! command_exists pipx; then
    sudo apt install pipx -y || pip install --user pipx
    pipx ensurepath
fi

if command_exists poetry; then
    echo -e "📦 Poetry já instalado."
    SKIPPED+=("Poetry")
else
    echo "Instalando Poetry via pipx..."
    if retry_command pipx install poetry; then
        INSTALLED_SUCCESS+=("Poetry")
    else
        INSTALLED_FAIL+=("Poetry")
    fi
fi

# ==========================================
# 4. Configuração do Projeto
# ==========================================
echo -e "\n${BLUE}[4/6] Configurando dependências do projeto...${NC}"

# Força o PATH para garantir que o poetry seja achado se acabou de ser instalado
export PATH=$PATH:$HOME/.local/bin

poetry config virtualenvs.in-project true

echo "Instalando dependências (poetry install)..."
if retry_command poetry install; then
    INSTALLED_SUCCESS+=("Project Deps (Poetry)")
else
    INSTALLED_FAIL+=("Project Deps (Poetry)")
fi

# Tentar instalar requirements.txt como fallback ou complemento se existir
if [ -f "requirements.txt" ]; then
    echo "Encontrado requirements.txt. Instalando via pip no ambiente virtual..."
    # Usa o pip do poetry run para garantir que vai para o venv
    poetry run pip install -r requirements.txt
fi

# ==========================================
# 5. Pre-commit
# ==========================================
echo -e "\n${BLUE}[5/6] Configurando Pre-commit...${NC}"

if retry_command poetry run pre-commit install; then
    INSTALLED_SUCCESS+=("Pre-commit Hooks")
else
    # Fallback global
    if ! command_exists pre-commit; then
        pipx install pre-commit
    fi
    pre-commit install
fi

# ==========================================
# RELATÓRIO FINAL
# ==========================================
echo -e "\n${BLUE}==========================================${NC}"
echo -e "${BLUE}       RELATÓRIO RASPBERRY PI             ${NC}"
echo -e "${BLUE}==========================================${NC}"

echo -e "\n${GREEN}✅ SUCESSOS:${NC}"
for item in "${INSTALLED_SUCCESS[@]}"; do echo -e "   ✔ $item"; done

echo -e "\n${YELLOW}⏭️  PULADOS (Existentes):${NC}"
for item in "${SKIPPED[@]}"; do echo -e "   - $item"; done

echo -e "\n${RED}❌ ERROS:${NC}"
if [ ${#INSTALLED_FAIL[@]} -eq 0 ]; then
    echo "   Nenhum erro. Parabéns!"
else
    for item in "${INSTALLED_FAIL[@]}"; do echo -e "   ✘ $item"; done
fi
echo -e "${BLUE}==========================================${NC}"

echo -e "Para ativar o ambiente, rode:"
echo -e "👉 ${YELLOW}poetry shell${NC}"