#!/bin/bash

# ==========================================
# Configurações e Cores
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arrays para o relatório final
INSTALLED_SUCCESS=()
INSTALLED_FAIL=()
SKIPPED=()

echo -e "${BLUE}=== Iniciando Script de Instalação Automatizada (Python 3.12 & Poetry) ===${NC}"

# ==========================================
# Funções Auxiliares
# ==========================================

# Função de Retry (Redundância)
# Tenta rodar um comando até 3 vezes se falhar
retry_command() {
    local n=1
    local max=3
    local delay=2
    while true; do
        "$@" && return 0
        if [[ $n -lt $max ]]; then
            ((n++))
            echo -e "${YELLOW}Comando falhou. Tentativa $n/$max em $delay segundos...${NC}"
            sleep $delay;
        else
            echo -e "${RED}O comando falhou após $n tentativas.${NC}"
            return 1
        fi
    done
}

# Função para instalar pacotes via APT com verificação
install_apt() {
    local package_name=$1
    
    if dpkg -l | grep -q "^ii  $package_name "; then
        echo -e "📦 $package_name já está instalado."
        SKIPPED+=("$package_name (APT)")
    else
        echo -e "⬇️  Instalando $package_name..."
        if retry_command sudo apt install -y "$package_name"; then
            echo -e "${GREEN}✔ $package_name instalado com sucesso.${NC}"
            INSTALLED_SUCCESS+=("$package_name (APT)")
        else
            echo -e "${RED}✘ Falha ao instalar $package_name.${NC}"
            INSTALLED_FAIL+=("$package_name (APT)")
        fi
    fi
}

# Função para verificar comando existente
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ==========================================
# 1. Atualização do Sistema
# ==========================================
echo -e "\n${BLUE}[1/5] Atualizando lista de pacotes...${NC}"
if retry_command sudo apt update; then
    INSTALLED_SUCCESS+=("Update APT")
else
    INSTALLED_FAIL+=("Update APT")
    # Se não atualizar o apt, é arriscado continuar, mas tentaremos
fi

install_apt "software-properties-common"
install_apt "curl" # Útil para baixar scripts se necessário

# ==========================================
# 2. Instalação do Python 3.12
# ==========================================
echo -e "\n${BLUE}[2/5] Configurando Python 3.12...${NC}"

# Adiciona repositório apenas se necessário
if ! grep -q "deadsnakes/ppa" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
    echo "Adicionando PPA deadsnakes..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
fi

install_apt "python3.12"
install_apt "python3.12-venv"
install_apt "python3.12-dev"

# Verificar versão
if command_exists python3.12; then
    PY_VERSION=$(python3.12 --version)
    echo -e "${GREEN}✔ Python detectado: $PY_VERSION${NC}"
else
    INSTALLED_FAIL+=("Binário Python 3.12 não encontrado")
fi

# ==========================================
# 3. Gerenciamento de Dependências (Poetry/Pipx)
# ==========================================
echo -e "\n${BLUE}[3/5] Configurando Poetry e Pipx...${NC}"

install_apt "pipx"
ensure_path=$(pipx ensurepath)

if command_exists poetry; then
    echo -e "📦 Poetry já está instalado."
    SKIPPED+=("Poetry")
else
    echo "⬇️  Instalando Poetry via pipx..."
    if retry_command pipx install poetry; then
         INSTALLED_SUCCESS+=("Poetry")
    else
         INSTALLED_FAIL+=("Poetry")
    fi
fi

# ==========================================
# 4. Configuração do Projeto (Venv & Install)
# ==========================================
echo -e "\n${BLUE}[4/5] Configurando Ambiente do Projeto...${NC}"

# Configura o poetry para criar o venv dentro da pasta do projeto (mais organizado)
poetry config virtualenvs.in-project true

echo "Instalando dependências do projeto com Poetry..."
if retry_command poetry install; then
    INSTALLED_SUCCESS+=("Dependências do Projeto (Poetry)")
else
    INSTALLED_FAIL+=("Dependências do Projeto (Poetry)")
fi

# ==========================================
# 5. Configuração de Pre-commit
# ==========================================
echo -e "\n${BLUE}[5/5] Configurando Hooks Git (Pre-commit)...${NC}"

# Tenta rodar via poetry run, assumindo que pre-commit está no pyproject.toml
if retry_command poetry run pre-commit install; then
    INSTALLED_SUCCESS+=("Pre-commit Hooks")
else
    # Fallback: Tenta instalar via pip se não estiver no poetry
    echo "Falha via poetry. Tentando instalar pre-commit globalmente..."
    pipx install pre-commit
    if retry_command pre-commit install; then
        INSTALLED_SUCCESS+=("Pre-commit Hooks (Global)")
    else
        INSTALLED_FAIL+=("Pre-commit Hooks")
    fi
fi

# ==========================================
# RELATÓRIO FINAL
# ==========================================
echo -e "\n${BLUE}==========================================${NC}"
echo -e "${BLUE}           RELATÓRIO DE INSTALAÇÃO        ${NC}"
echo -e "${BLUE}==========================================${NC}"

echo -e "\n${GREEN}✅ SUCESSOS:${NC}"
if [ ${#INSTALLED_SUCCESS[@]} -eq 0 ]; then
    echo "   Nenhum item novo instalado."
else
    for item in "${INSTALLED_SUCCESS[@]}"; do
        echo -e "   ✔ $item"
    done
fi

echo -e "\n${YELLOW}⏭️  PULADOS (Já instalados):${NC}"
for item in "${SKIPPED[@]}"; do
    echo -e "   - $item"
done

echo -e "\n${RED}❌ ERROS/FALHAS:${NC}"
if [ ${#INSTALLED_FAIL[@]} -eq 0 ]; then
    echo "   Nenhum erro encontrado! 🎉"
else
    for item in "${INSTALLED_FAIL[@]}"; do
        echo -e "   ✘ $item"
    done
    echo -e "\n${RED}⚠ Verifique os logs acima para detalhes dos erros.${NC}"
fi

echo -e "\n${BLUE}==========================================${NC}"

# Aviso sobre o ambiente virtual
if [ ${#INSTALLED_FAIL[@]} -eq 0 ]; then
    echo -e "${GREEN}Tudo pronto! Para ativar seu ambiente, use:${NC}"
    echo -e "👉 ${YELLOW}poetry shell${NC} ou ${YELLOW}source .venv/bin/activate${NC}"
fi