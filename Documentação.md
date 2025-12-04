`node/routes/mining.py`

Essa é uma excelente iniciativa. Documentar o **"Porquê"** das coisas é o que diferencia um amontoado de código de uma Engenharia de Software robusta.

Para a sua equipe, o mais importante aqui não é apenas ler o código, mas entender o **Ciclo de Vida do Consenso**.

Preparei um resumo técnico focado em metodologia, pronto para você usar na sua documentação interna (Confluence, Notion, README), seguido do código refinado.

-----

# 📘 Documentação de Engenharia: Módulo de Mineração

## 1\. O Conceito de "Job Negotiation" (Negociação de Trabalho)

Diferente de sistemas centralizados onde o servidor envia ordens, na Blockchain usamos um modelo de **PULL**.

  * **O Minerador é o cliente:** Ele solicita trabalho (`GET /get_work`).
  * **O Node é o provedor:** Ele monta um "Template de Bloco" (Candidato).
  * **Estado:** O Node guarda esse template em memória (`mining_jobs`). Quando o minerador volta com a resposta (Nonce), o Node verifica se a resposta bate com o template que *ele* emitiu.

## 2\. Ajuste Dinâmico de Dificuldade (DAA)

Para manter o tempo médio de mineração constante (ex: 3 minutos), o protocolo ajusta a dificuldade a cada **Época (Epoch)**.

### A Lógica Matemática

O ajuste ocorre quando `block_height % INTERVAL == 0`.
A fórmula básica que utilizamos no Core é:

$$
Target_{novo} = Target_{atual} \times \frac{Tempo_{real}}{Tempo_{alvo}}
$$

  * **Tempo Real \< Tempo Alvo:** A rede está muito rápida (muitos mineradores). A dificuldade aumenta (Target diminui).
  * **Tempo Real \> Tempo Alvo:** A rede está lenta. A dificuldade diminui (Target aumenta).

-----

## 3\. Implementação de Referência (`node/routes/mining.py`)

Abaixo está a implementação da rota `/get_work` com a lógica de ajuste de dificuldade integrada.

**Melhorias aplicadas no código:**

1.  **Type Safety:** Conversão explícita de `dict` para objeto `Block` (pois o repositório geralmente retorna JSON/Dict).
2.  **Backtracking Seguro:** O loop para encontrar o `epoch_start_block` agora converte os dados recuperados do banco para objetos antes de acessar `.header`.
3.  **Sanity Checks:** Verificações para garantir que não estamos acessando blocos inexistentes.


### Pontos de Atenção para a Equipe

1.  **Performance do Backtracking:** O loop `for` que busca o `epoch_start_block` faz leitura em disco (`repo.get_block`).

      * *Agora (MVP):* Com intervalo de 10 blocos, é imperceptível.
      * *Futuro:* Se o intervalo for 2016 blocos (como no Bitcoin), isso travará a API. A solução futura é ter um índice no banco de dados que mapeia `Height -> Hash`, permitindo busca O(1) (`repo.get_block_by_height(start_height)`).

2.  **Job Expiration:** O `mining_jobs` é um dicionário em memória. Se o servidor reiniciar, os jobs somem e os mineradores terão seu trabalho rejeitado (o que é aceitável, eles pedirão um novo logo em seguida).

3.  **Segurança:** Validamos se o `repo.get_block` retornou dados antes de tentar converter, evitando crashes se o banco estiver corrompido.