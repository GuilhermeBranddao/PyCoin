from core.transaction import Transaction, TxInput, TxOutput


class TestTransaction:

    def test_create_transaction_structure(self, identity):
        """
        Testa se a estrutura básica e o cálculo do ID (Hash) estão consistentes.
        """
        _, address = identity

        # Cenário: Tenho um input de uma tx anterior (hash fake)
        tx_input = TxInput(prev_tx_id="a" * 64, output_index=0)
        tx_output = TxOutput(amount=50, address=address)

        tx = Transaction(inputs=[tx_input], outputs=[tx_output])

        # Assertions
        assert tx.id is not None
        assert len(tx.id) == 64  # SHA256 hex string
        assert len(tx.inputs) == 1
        assert tx.inputs[0].signature == ""  # Ainda não assinada

        # Determinismo: O mesmo conteúdo deve gerar o mesmo ID
        tx2 = Transaction(inputs=[tx_input], outputs=[tx_output], timestamp=tx.timestamp)
        # Forçamos o recálculo/atribuição pois o ID é gerado no post_init
        tx2.id = tx2.calculate_hash()

        assert tx.id == tx2.id

    def test_sign_and_verify_valid_transaction(self, identity):
        """
        Testa o fluxo feliz: Assinar um input e validar a transação.
        """
        private_key, my_address = identity
        receiver_address = "b" * 64

        # 1. Arrange (Preparação)
        inp = TxInput(prev_tx_id="feed" * 16, output_index=0)
        out = TxOutput(amount=10, address=receiver_address)
        tx = Transaction(inputs=[inp], outputs=[out])

        # 2. Act (Ação)
        # Assinar o input 0 com minha chave privada
        tx.sign_input(0, private_key)

        # 3. Assert (Verificação)
        assert inp.signature != ""
        assert inp.public_key != ""
        assert tx.is_valid() is True

    def test_transaction_tampering_fails(self, identity):
        """
        Segurança: Se eu alterar o valor de saída APÓS assinar, 
        a validação deve falhar (O hash muda e a assinatura não bate mais).
        """
        private_key, _ = identity

        inp = TxInput(prev_tx_id="aaaa" * 16, output_index=0)
        out = TxOutput(amount=10, address="receiver_addr")
        tx = Transaction(inputs=[inp], outputs=[out])

        # Assina corretamente
        tx.sign_input(0, private_key)
        assert tx.is_valid() is True

        # ATAQUE: Hacker tenta mudar o valor de 10 para 100
        tx.outputs[0].amount = 100

        # O ID da transação mudaria se recalculado.
        # is_valid verifica se ID atual bate com o conteudo E se a assinatura bate com o ID.
        # Mesmo se o hacker atualizar o ID, a assinatura antiga não validará o novo ID.

        # Opção A: Hacker não atualiza o ID -> Falha na checagem de integridade do hash
        assert tx.is_valid() is False

        # Opção B: Hacker atualiza o ID -> Falha na verificação da assinatura (assinou hash antigo)
        tx.id = tx.calculate_hash()
        assert tx.is_valid() is False

    def test_create_coinbase_transaction(self):
        """
        Testa a criação da transação de recompensa (sem inputs reais).
        """
        miner_address = "miner_wallet_addr"
        tx = Transaction.create_coinbase(miner_address, block_height=100, reward=50)

        assert len(tx.inputs) == 1
        assert len(tx.outputs) == 1
        assert tx.inputs[0].prev_tx_id == "00000000"
        assert tx.inputs[0].output_index == 100
        assert tx.outputs[0].amount == 50

        # Transações coinbase são válidas por definição no método is_valid
        # (se você implementou a lógica de pular validação de assinatura para prev_tx_id zero)
        # No seu código transaction.py:
        # if inp.prev_tx_id == "00000000": continue
        assert tx.is_valid() is True
