pycoin/
│
├── node/                       # O SOFTWARE DO NÓ (Servidor) Full Node (API, rede, sincronização)
│   ├── __init__.py
│   ├── app.py                  # FastAPI ou HTTP server
│   ├── routes/                 # Rotas do node
│   │   ├── __init__.py
│   │   ├── blocks.py           # /blocks, /chain, /submit_block
│   │   ├── mempool.py          # /mempool
│   │   ├── tx.py               # /tx/new
│   │   ├── peers.py            # /peers, /connect
│   ├── services/               # Camada de serviços (não misturar com core)
│   │   ├── mempool_service.py
│   │   ├── sync_service.py
│   │   ├── validation_service.py
│   ├── storage/
│   │   ├── chain.json
│   │   ├── mempool.json       # Área de "staging"
│   │   └── peers.json
│
│
├── miner_client/                      # Minerador (software separado)
│   ├── __init__.py
│   ├── miner.py                # Script principal de mineração
│   ├── pow.py                  # Funções de PoW
│   └── worker.py               # Threads/CPU paralelos (opcional)
│
├── wallet_client/                     # Cliente wallet (usado pelo usuário final)
│   ├── __init__.py
│   ├── wallet.py               # Gera chaves, endereços
│   ├── signer.py               # Assina transações
│   ├── cli.py                  # CLI opcional (create-wallet, send-tx)
│   └── utils.py
│
├── core/                       # Lógica da blockchain (nunca depende do node)
│   ├── __init__.py
│   ├── block.py                # Estrutura do bloco + header (→ define bloco)
│   ├── blockchain.py           # Blockchain, difficulty adjust, validation
│   ├── transaction.py          # Transação
│   ├── utxo.py                 # UTXO Set (Bitcoin-like)
│   ├── pow.py                  # Hashing, difficulty target
│   ├── crypto.py               # ECDSA, hashing, signatures
│   └── merkle.py               # Merkle tree
│
├── docs/
│   ├── architecture.md         # Documentação da arquitetura
│   ├── api-spec.md             # Rotas da API
│   ├── mining-spec.md          # Processo de mineração
│   └── tx-lifecycle.md         # Ciclo de vida de uma transação
│
├── scripts/                    # Ferramentas auxiliares
│   ├── generate_genesis.py
│   ├── sync_nodes.py
│   └── benchmark_pow.py
│
├── notebooks/                  # Notebooks Jupyter para testes
│   ├── test_transactions.ipynb
│   ├── test_mining.ipynb
│   └── test_network.ipynb
│
├── tests/                      # Testes unitários
│   ├── test_block.py
│   ├── test_pow.py
│   ├── test_tx.py
│   ├── test_blockchain.py
│   └── test_wallet.py
│
├── config.py                 # Configurações globais (Pydantic Settings)
├── requirements.txt or pyproject.toml
├── README.md
└── .env (opcional)



# Requisitos:

## Constituição

### Core (Regras)
- O core/ contém as Regras de Consenso. Ele não deve saber o que é HTTP, não deve saber o que é FastAPI, nem o que é um banco de dados SQL ou JSON.
- A Regra de Ouro: Você deve ser capaz de importar o core tanto no node/ quanto no miner_client/ sem arrastar dependências de rede.
- O que vive aqui: A matemática pura. calculate_hash, verify_signature, calculate_merkle_root. Se o Bitcoin mudasse de TCP para pombo-correio, o core não mudaria uma linha de código.

- Isso permite que você faça coisas avançadas no futuro, como:
    - Mineradores em C++/Rust: Se a lógica matemática está isolada, você pode reescrever apenas o miner_client em uma linguagem de baixo nível para performance, mantendo o Node em Python, desde que respeitem o protocolo de dados definido no core.
    - Testes Determinísticos: Você consegue testar cenários de Fork, Double Spend e Reorg apenas instanciando classes do core, sem precisar subir um servidor HTTP.

### core/transaction.py
É o componente mais complexo matematicamente do `core/`
No modelo UTXO, uma transação não diz "Alice envia 5 para Bob". Ela diz:

1. Inputs: "Estou destrancando estes cofres antigos (outputs de transações passadas) que pertencem a mim."
2. Outputs: "Estou criando novos cofres (novos outputs) com estes valores, trancados com o endereço do Bob."

### Merkle Tree (Otimização para o Minerador) (core/merkle.py)
Você mencionou "State of the Art" para core/merkle.py. Isso é crucial para o seu módulo miner_client.
Por que? O minerador não precisa receber o bloco inteiro com 2000 transações.
1. O Node recebe as transações.
2. O Node monta a Merkle Tree.
3. O Node envia apenas a Merkle Root (32 bytes) no Header para o Minerador.
4. O Minerador trabalha apenas no Header.

Isso economiza banda de rede drasticamente. Sua arquitetura suporta isso perfeitamente, pois miner_client só precisa importar core.block (para estruturar o header) e core.pow.

A Merkle Tree permite resumir 2.000 transações em uma única string de 32 bytes (a merkle_root). Se um único bit de uma transação mudar, a raiz muda completamente, invalidando o bloco.

### A Estrutura do Bloco: core/block.py
Aqui aplicamos a separação vital:
1. BlockHeader: Dados leves (80 bytes no Bitcoin) que o minerador usa.
2. Block: O contêiner completo que o Full Node armazena.

1. Por que `serialize_for_mining` usa `struct`?
    - Consistência: Python pode serializar inteiros de formas diferentes. `struct.pack('<I...')` garante que um inteiro de 4 bytes seja sempre 4 bytes, Little-Endian.
    - Interoperabilidade: Se você escrever seu minerador em C ou Rust no futuro, eles lerão exatamente esses bytes.
2. Separação Header/Body:
    - Quando seu Node receber um pedido de `get_headers` (para sincronização rápida), você envia apenas a lista de `BlockHeader`, economizando 99% da banda de rede.
    - O minerador recebe apenas os 80 bytes do header, não o bloco de 1MB.
3. Segurança do Merkle Root:
    - No método `create_candidate`, calculamos a raiz antes de criar o header. Isso "congela" a lista de transações. Se alguém tentar adicionar uma transação depois, a raiz muda e o hash do bloco (PoW) torna-se inválido.


### core/blockchain.py
É o "árbitro" do sistema. É ele que diz se um bloco é válido ou se um minerador está tentando trapacear.

Aqui consolidamos as Regras de Consenso (Consensus Rules). Se você mudar uma linha aqui (ex: mudar o tempo de 3 para 2 minutos), você cria um Hard Fork (uma nova moeda incompatível).

Este arquivo implementa a lógica do Target (o "alvo" do PoW) e a validação temporal (para evitar ataques de timestamp).

Por que essa implementação é robusta?
Proteção contra Time Warp: No método validate_block, adicionei verificações de timestamp.

Sem isso, um minerador poderia mentir sobre a hora (dizer que levou 1 segundo para minerar) para fazer a dificuldade explodir, ou dizer que levou 10 horas para a dificuldade cair para zero e minerar 1000 blocos em um minuto.

Aritmética de Target (Bits): A classe DifficultyEngine lida com a conversão estranha de bits (float compactado) para inteiros gigantes. Isso é exatamente como o Bitcoin economiza espaço no header.

Se o tempo real < tempo alvo/4, limitamos o ajuste. Isso impede oscilações brutais se a rede de mineração dobrar de tamanho da noite para o dia.

Stateless: A classe BlockchainRules não guarda estado. Você passa (block, previous_block) e ela responde. Isso torna os testes unitários triviais e permite validação paralela.

---


### A Mudança de Paradigma: UTXO (Unspent Transaction Output).
- O Desafio: Isso é muito mais difícil de implementar. Você não tem uma tabela users com colunas balance.
- A Lógica: Você tem um "lago" de moedas não gastas.
- Para gastar 5 moedas, você precisa pescar uma UTXO de 2 e uma UTXO de 4 (total 6).
- Você cria uma transação que consome essas duas (inputs) e cria duas novas saídas: 5 para o destino e 1 de troco para você.
- Dica: Seu storage/chain.json vai ficar pesado rápido. Para o UTXO set, considere usar SQLite ou LevelDB (mesmo que didático), pois você precisará consultar "quais UTXOs pertencem ao endereço X" muito rápido.

- A Armadilha do UTXO:Muitos iniciantes tentam calcular o saldo iterando a blockchain inteira toda vez. Isso é $O(N)$.A Solução Sênior: Você precisa manter um UTXO Set (o "Chainstate").No seu node/storage/, além do chain.json (que é o histórico), você precisará de um índice separado. Sugiro fortemente usar SQLite ou LevelDB (o Bitcoin usa LevelDB) para o UTXO Set, mesmo que didático Estrutura de Dados sugerida para o UTXO:A chave primária de uma moeda não é o "dono", é a transação que a criou.


### O Node como Gateway (`node/`)
- Routes: Apenas recebem o JSON, validam o formato (Pydantic) e passam para o service.
- Services: Orquestram. Exemplo no blocks.py:
    - Recebe bloco.
    - Chama core.block.verify_block() (Validação pura).
    - Chama core.pow.verify_pow() (Validação matemática).
    - Se válido, chama storage para salvar.
    - Chama p2p_service para propagar.


### config.py
- Consensus Params (No core): Devem ser constantes ou classes imutáveis. Ex: BLOCK_TIME = 180, HALVING_INTERVAL = 210000. Todos os nós devem concordar com isso.
- Node Settings (No node): Coisas locais. Ex: DB_PATH, SERVER_PORT, PEERS_LIST.


### mempool.json
Quando uma transação chega (/tx/new), o Node deve validar a assinatura imediatamente usando core/crypto.py antes de aceitar na mempool. Isso evita spam.


## Engenharia de sistemas (Coração da Persistência)
Para um blockchain funcionar, você precisa de duas estruturas de dados rodando em paralelo:
1. Blockchain (Histórico): A pilha de blocos (imutável).
2. UTXO Set (Estado Atual): O "banco de dados" de quem tem dinheiro agora.

Se você não persistir o UTXO Set separadamente, terá que reprocessar toda a blockchain a cada reinício do servidor (o que levaria horas em produção).

1. Camada de Persistência: `node/storage/database.py`
Vamos usar SQLite. É robusto, ACID (Atomicidade, Consistência, Isolamento, Durabilidade) e perfeito para nós que não precisam de escala industrial (como o Bitcoin Core usa LevelDB, mas SQLite funciona muito bem até alguns GBs).

Nesta classe, implementaremos o Gerenciamento Atômico: Quando um bloco é salvo, atualizamos o UTXO set na mesma transação de banco de dados. Se falhar, nada é salvo.

### Mempool (Fila)
2. O Guardião das Transações: `node/services/mempool_service.py`
A Mempool (Memory Pool) é a sala de espera. As transações ficam aqui na memória RAM até serem pegas por um minerador.

Se deixarmos entrar lixo aqui, o minerador vai gastar energia processando transações inválidas e o bloco dele será rejeitado pela rede.

Regras de Ouro da Mempool:
1. Só aceita transações com assinatura válida (Stateless check).
2. Só aceita transações cujos inputs existem no UTXO set (Stateful check).
3. Evita gasto duplo (não aceita duas transações gastando o mesmo input).


### Storage (Persistência Profissional)
3. O Cofre Forte: `node/storage/` com LevelDB
Aqui vamos implementar o padrão profissional híbrido:
1. `blocks.dat`: Arquivo bruto (Append Only). Guarda o bloco inteiro.
2. LevelDB: Guarda apenas os índices e o estado (UTXO).

- `b-{block_hash}` -> `(file_number, offset, length)` (Onde está o bloco no disco?)
- `u-{txid}-{index}` -> `(amount, pubkey_hash)` (UTXO Set)
- `H-last_hash` -> Hash do último bloco (Tip)

Instalação Necessária: Você precisará da lib plyvel (wrapper Python para LevelDB). pip install plyvel (no linux) ou usar o poetry add python-rocksdb (para o windows)



































✔ Separação 100% real entre Node / Miner / Wallet
Exatamente como acontece no Bitcoin:
- O node valida a blockchain.
- O miner roda PoW e tenta construir blocos.
- A wallet só cria e assina transações.

✔ Rotas FastAPI ficam isoladas e limpas
Nada de misturar blockchain com API.
Cada rota chama uma camada de serviço.

✔ Módulo para UTXO
É onde você controla:
- inputs
- outputs
- gasto duplo
- coinbase transaction
- saldo real

estrutura é escalável
Ela permite futuramente:
- P2P com websockets
- Banimento de peers maliciosos
- UTXO persistido em LevelDB
- Sistema de fees e mempool por prioridade
- PoW multi-thread
- Pool mining básico