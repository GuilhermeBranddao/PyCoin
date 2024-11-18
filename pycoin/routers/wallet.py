from fastapi import APIRouter

from pycoin.schemas import AddTransaction
from pycoin.transaction import Transaction
from pycoin.wallet import Wallet

router = APIRouter(prefix='/wallet', tags=['wallet'])


@router.get('/generate_wallet')
def generate_wallet():
    try:
        wallet = Wallet()
        private_key, public_key, address = wallet.generate_strings_key_no_markers()

        # app.logger.info(f'Carteira gerada com sucesso. Address: {address}')

        response = {
            'message': 'Dados da sua carteira gerados com sucesso!',
            'private_key': private_key,
            'public_key': public_key,
            'address': address,
        }
        return response

    except Exception as e:
        # app.logger.error(f'Erro ao gerar carteira: {e}')

        response = {
            'message': 'Erro ao gerar os dados da carteira. Tente novamente mais tarde.',
            'error': str(e),
        }
        return response


@router.post('/get_balance_and_transactions')
def get_balance_and_transactions():
    pass


@router.post('/add_transaction')
def add_transaction(add_transaction: AddTransaction):

    transaction = Transaction()

    transaction.add_transaction(private_key_sender=add_transaction.private_key_sender,
                                public_key_sender=add_transaction.public_key_sender,
                                recipient_address=add_transaction.recipient_address,
                                amount=add_transaction.amount,)

    response = {'message': 'Nova transação adicionada'}

    return response
