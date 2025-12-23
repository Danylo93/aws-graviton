#!/bin/sh

###################################################
##############        INFO      ###################
# Para testar localmente
# Este script auxilia no gerenciamento de variáveis de ambiente
# em um arquivo .env. Ele suporta a conversão de JSON para o formato .env,
# manipulação de variáveis e execução de tarefas pós-boot.
###################################################

# Define o caminho do arquivo .env
if [ -n "$GITHUB_WORKSPACE" ]; then
    ENV_PATH="${GITHUB_WORKSPACE}/.env"
else
    ENV_PATH='../.env'
fi

###################################################
# Função: post_boot
# Executa tarefas específicas após o boot do sistema.
# Carrega o arquivo .env e realiza operações específicas no ambiente.
###################################################
post_boot() {
    # Esta função será chamada somente dentro do container docker no ambiente de produção e homologação.
    # Adicione ou remova funções conforme necessário para o seu microsserviço.
    
    # Carrega o arquivo .env para o escopo da função
    if [ -f "$ENV_PATH" ]; then
        # shellcheck disable=SC1090
        source "$ENV_PATH"
    else
        echo "Erro: Arquivo .env não encontrado em $ENV_PATH" >&2
        return 1
    fi

    # Executa migrações do banco de dados com poetry e alembic
    poetry run alembic upgrade head
}

###################################################
# Função: convert_json_to_env
# Converte uma string JSON para o formato .env
# Argumentos:
#   $1 - String JSON a ser convertida
###################################################
convert_json_to_env() {
    local json_string="$1"

    echo "JSON Recebido: $json_string" >&2  # Log JSON recebido para depuração

    # Valida se o JSON é válido
    if ! echo "$json_string" | jq empty; then
        echo "Erro: JSON inválido fornecido!" >&2
        return 1
    fi

    # Converte JSON para o formato KEY="VALUE" e insere no .env
    while IFS= read -r line; do
        upsert_env "$line"
    done < <(echo "$json_string" | jq -r 'to_entries | map("\(.key)=\(.value|tostring)") | .[]')
}

###################################################
# Função: remove_env_suffix
# Remove sufixos como _HML ou _PROD das chaves
# Argumentos:
#   $1 - Chave para ser processada
###################################################
# remove_env_suffix() {
#     local key="$1"

#     # Se REMOVE_SUFIX estiver vazio, retorna a chave como está
#     if [ -z "$REMOVE_SUFIX" ]; then
#         echo "$key"
#         return
#     fi

#     # Remove o sufixo da chave, se existir
#     case "$key" in
#         *"$REMOVE_SUFIX")
#             key=$(echo "$key" | sed "s/$REMOVE_SUFIX//")
#             ;;
#     esac

#     echo "$key"
# }

###################################################
# Função: remove_env_suffix
# Remove sufixos como _HML, _PRD ou _DEV das chaves.
# Se a chave terminar com um dos sufixos (DEV, HML ou PRD)
# mas não for o especificado em REMOVE_SUFIX, retorna vazio.
# Argumentos:
#   $1 - Chave para ser processada
###################################################
remove_env_suffix() {
    local key="$1"

    # Se REMOVE_SUFIX estiver vazio, retorna a chave como está
    if [ -z "$REMOVE_SUFIX" ]; then
        echo "$key"
        return
    fi

    # Verifica se a chave termina com um dos sufixos válidos (_DEV, _HML ou _PRD)
    case "$key" in
        *_DEV|*_HML|*_PRD)
            # Se a chave termina com o sufixo desejado, remove-o
            case "$key" in
                *"$REMOVE_SUFIX")
                    # Remove o sufixo _${REMOVE_SUFIX} usando expansão de parâmetros
                    key=$(echo "$key" | sed "s/$REMOVE_SUFIX//")
                    ;;
                *)
                    # Se termina com outro sufixo, retorna vazio para ignorar a variável
                    key=""
                    ;;
            esac
            ;;
        *)
            # Se não terminar com nenhum dos três, mantém a chave original
            ;;
    esac

    echo "$key"
}


###################################################
# Função: upsert_env
# Adiciona ou atualiza variáveis no arquivo .env
# Argumentos:
#   Lista de argumentos no formato KEY=VALUE
###################################################
upsert_env() {
    # Cria o arquivo .env se ele não existir
    if [ ! -f "$ENV_PATH" ]; then
        echo "Criando arquivo .env em $ENV_PATH"
        touch "$ENV_PATH"
    fi

    for ARG in "$@"; do
        local key=$(echo "$ARG" | cut -d '=' -f 1)
        # Captura o valor preservando tudo após o primeiro "="
        local value=$(echo "$ARG" | sed "s/^[^=]*=//")

        # Remove sufixos do KEY conforme o REMOVE_SUFIX passado (_DEV _HML _PROD etc)
        key=$(remove_env_suffix "$key")

        # Ignora se a chave está vazia
        if [ -z "$key" ]; then
            continue
        fi

        # Trata o valor conforme o tipo
        if [ "$value" = "null" ] || [ -z "$value" ] || [ "$value" = "\"\"" ]; then
            value=""
        elif echo "$value" | grep -Eq '^[+-]?[0-9]+(\.[0-9]+)?$'; then
            # Valor numérico
            value="$value"
        elif [ "$value" = "true" ] || [ "$value" = "false" ]; then
            # Valor booleano
            value="$value"
        elif echo "$value" | grep -Eq '^\{.*\}$|^\[.*\]$'; then
            # Se for JSON (começa com { ou [ e termina com } ou ])
            value="'$value'"
        else
            # Valor string, adiciona aspas
            value="\"$value\""
        fi

        # Atualiza ou adiciona a chave no arquivo .env
        if grep -q "^$key=" "$ENV_PATH"; then
            sed -i.bak "s|^$key=.*|$key=$value|" "$ENV_PATH"
        else
            echo "$key=$value" >> "$ENV_PATH"
        fi
    done
}