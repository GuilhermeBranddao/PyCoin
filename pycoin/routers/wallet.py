from fastapi import APIRouter

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
