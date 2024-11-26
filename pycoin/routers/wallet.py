from fastapi import APIRouter

from pycoin.blockchain.block_utils import load_chain
from pycoin.schemas.schemas import AddTransaction, BalanceRequest
from pycoin.settings.settings import Settings
from pycoin.transaction import Transaction
from pycoin.wallet import Wallet

settings = Settings()
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


@router.post('/balance_and_transactions')
def balance_and_transactions(request: BalanceRequest):

    transaction = Transaction()

    address_transaction = transaction.check_wallet_balance(
        blockchain=load_chain(block_file_path=settings.BLOCKCHAIN_FILE),
        wallet_address=request.address)

    return address_transaction


@router.post('/add_transaction')
def add_transaction(add_transaction: AddTransaction):

    transaction = Transaction()
    chain = load_chain(block_file_path=settings.BLOCKCHAIN_FILE)
    transaction.add_transaction(private_key_sender=add_transaction.private_key_sender,
                                public_key_sender=add_transaction.public_key_sender,
                                recipient_address=add_transaction.recipient_address,
                                amount=add_transaction.amount,
                                chain=chain)

    response = {'message': 'Nova transação adicionada'}

    return response
