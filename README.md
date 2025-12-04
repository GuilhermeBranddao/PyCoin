# PyCoin
PyCoin é uma aplicação blockchain local para aprendizado e experimentação.

A tecnologia blockchain revolucionou a forma como transações digitais são registradas, validadas e compartilhadas, tornando-se a base de criptomoedas, sistemas financeiros descentralizados, cadeias de suprimentos e muito mais.

Meu objetivo com esse projeto é aprender a construir uma blockchain do zero é uma e entender profundamente os mecanismos de segurança, consenso e descentralização que sustentam esse ecossistema, e futuramente desenvolver novas funcionalidades e expandir meu conhecimento sobre o asunto

Este guia o ajudará a configurar e rodar o projeto em sua máquina.

## Instalações

### Passo 1: Clonar o repositório
Clone o repositório do projeto para sua máquina local:

`https://github.com/GuilhermeBranddao/PyCoin.git`

### Passo 2: Instalar dependências
Escolha o método de instalação conforme o sistema operacional:

#### Para Linux:

Dê permissão de execução: 
`chmod +x install/install_v1.1.sh`

Execute o script de instalação:

`. install/install_v1.1.sh`

#### Para Windows:
1. Baixe e instale o [Python 3.12](https://www.python.org/downloads/release/python-3120/).
2. Execute o arquivo de instalação:

`install\install.bat`

3. Instale as dependencias do poetry:

`poetry install`

### Passo 3: Verifique se está tudo OK
1. Execute os testes

`task test`

Se tudo deu certo, rode a aplicação com o seguinte comando:

`task run`


Criar (Gênesis)
`python scripts/init_blockchain.py`

Se você alterar a dificuldade ou outra coisas (TODO: liscar coisas) você deve gerar um novo bloco genesis
`python scripts/init_blockchain.py --force`
`python scripts/init_blockchain.py --port 8000 --force`

Rodar API
`uvicorn node.app:app --reload --port 8000`

Rode a Wallet:
`python wallet_client/simple_wallet.py`

- Ela vai gerar um arquivo my_private_key.pem.
- Ela vai mostrar seu Endereço no terminal. Copie esse endereço.

#### Minerador
Mude a variável MINER_ADDRESS para o endereço que a Wallet acabou de mostrar.

Rode o Minerador
`python miner_client/miner.py`

- Agora você está minerando para a sua carteira real!


  
Pronto, agora você está rodando uma verção do PyCoin localmente em sua maquina, para uma interface amigavel, acesse o [link](http://127.0.0.1:8000/docs) para ter acesso os endpoits e conseguir acesar as funcionalidades.

## **Como usar o projeto**




## **Observações**
- Esse projeto surgiu da minha vontade de aprender como a blockchain/criptomoedas funcionam e junto a isso a minha vontade de publicar tudo o que eu venho a anos estudando, acredito que não há maneira melhor de testar o seu conhecimento.

- O projeto ainda está em fase de desenvolvimento, novas melhorias e funcionalidades estão sendo implementadas.

- Feedbacks e contribuições são bem-vindos para tornar o PyCoin ainda melhor.

---
## **Referências**

Este projeto foi inspirado pelos seguintes autores

Ideia do projeto veio do livro [Blockchain e Criptomoedas com Python](https://www.amazon.com.br/Blockchain-Criptomoedas-Python-Fernando-Feltrin-ebook/dp/B0935BY1V5/ref=pd_ci_mcx_mh_mcx_views_0_title).

Utilização do poery, fastAPI, criação de testes e entre outras coisas veio do [@dunossauro](https://dunossauro.com/), tanto pelo seu canal do youtube [Eduardo Mendes](https://www.youtube.com/@Dunossauro) quanto do seu site/projeto [FastApi do zero](https://fastapidozero.dunossauro.com/)

---

Caso tenha dúvidas ou encontre problemas, entre em (contato)[guilhermebranddao@gmail.com] ou abra uma issue no repositório. 🚀
