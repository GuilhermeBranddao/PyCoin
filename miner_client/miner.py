import hashlib
import struct
import sys
import time
from urllib.parse import urlparse, urlunparse

import requests

from config import MINER_ADDRESS, NODE_URL


def solve_pow(job):
    """
    O Loop Quente (Hot Loop). É aqui que a CPU vai fritar.
    Tenta encontrar um Nonce que satisfaça: Hash(Header) < Target
    """
    job_id = job['job_id']
    target = int(job['target'], 16)  # Converte string hex "0x000..." para int

    # Preparação dos dados estáticos (tudo que NÃO muda no loop)
    # Isso evita recriar bytes a cada iteração, ganhando performance.
    version = job['version']
    prev_hash_bytes = bytes.fromhex(job['prev_hash'])
    merkle_root_bytes = bytes.fromhex(job['merkle_root'])
    timestamp = job['timestamp']
    bits = job['bits']

    print(f"⛏️  Minerando Job {job_id[:8]}...")
    print(f"🎯 Target (Int): {target}")

    # Nonce começa em 0
    nonce = 0
    start_time = time.time()
    last_report_time = start_time
    hashes_tried = 0

    # Empacota a primeira parte do cabeçalho (80 bytes no total, menos 4 do nonce)
    # Formato Little-Endian (<): Version(I), PrevHash(32s), Merkle(32s), Time(I), Bits(I)
    # TOTAL: 4 + 32 + 32 + 4 + 4 = 76 bytes
    static_header = struct.pack(
        '<I32s32sII',
        version,
        prev_hash_bytes,
        merkle_root_bytes,
        timestamp,
        bits
    )
    print(f"DEBUG: Target Hex: {hex(target)}")
    while True:
        # 1. Telemetria em Tempo Real (A cada 3 segundos)
        current_time = time.time()
        if current_time - last_report_time > 3:
            hashrate = hashes_tried / (current_time - start_time)
            print(f"🔨 Hashrate: {hashrate / 1000:.2f} kH/s | Nonce: {nonce}")
            last_report_time = current_time

        # 1. Checa se devemos desistir (ex: demorou muito, peça trabalho novo)
        # if time.time() - start_time > 30:
        #     print(f"⌛ Job expirou (10s). Hashrate: {hashes_tried / 10:.2f} H/s")
        #     return None
        # if nonce % 1000 == 0:
        if time.time() - start_time > 300:
            print(f"⌛ Job expirou. Hashrate: {hashes_tried / 10:.2f} H/s")
            return None

        # 2. Empacota o Nonce (4 bytes) e junta com o cabeçalho
        nonce_bytes = struct.pack('<I', nonce)
        full_header = static_header + nonce_bytes

        # 3. Double SHA-256
        hash1 = hashlib.sha256(full_header).digest()
        hash2 = hashlib.sha256(hash1).digest()

        # 4. Verifica o Target (Código Realista do Bitcoin)
        # O Bitcoin compara o hash como Little-Endian convertido para Big-Int.
        result_int = int.from_bytes(hash2[::-1], 'big')

        # print("result_int:", result_int)
        if result_int <= target:
            # 5. SUCESSO!
            end_time = time.time()
            duration = end_time - start_time
            print(f"\n💎 BLOCO ENCONTRADO! Nonce: {nonce}")
            print(f"⚡ Hash: {result_int}")
            print(f"⚡ Hex: {hash2[::-1].hex()}")
            print(f"⏱️ Tempo: {duration:.2f}s | Média: {hashes_tried / duration:.2f} H/s")

            return {
                "job_id": job_id,
                "nonce": nonce,
                "timestamp": timestamp
            }

        nonce += 1
        hashes_tried += 1

        # Limite de 32 bits do nonce (4 bilhões)
        if nonce > 0xFFFFFFFF:
            return None


def start_miner(node_url: str = None):
    # Usa o node_url passado ou a constante importada
    node_url = node_url or NODE_URL
    print(f"🔌 Conectando ao Node em {node_url}")
    print(f"💰 Recompensas irão para: {MINER_ADDRESS}")
    print("-" * 40)

    while True:
        try:
            # 1. Pedir trabalho
            response = requests.get(
                f"{NODE_URL}/mining/get_work",
                params={"miner_address": MINER_ADDRESS}
            )

            if response.status_code != 200:
                print(f"⚠️  Node retornou erro: {response.text}")
                time.sleep(5)
                continue

            job = response.json()

            # 2. Tentar resolver
            solution = solve_pow(job)

            # 3. Se resolveu, enviar
            if solution:
                print("🚀 Enviando solução para o Node...")
                submit_res = requests.post(f"{NODE_URL}/mining/submit_work", json=solution)

                if submit_res.status_code == 200:
                    print("✅ Bloco ACEITO pela rede!")
                else:
                    print(f"❌ Bloco REJEITADO: {submit_res.text}")

        except requests.exceptions.ConnectionError:
            print("❌ Erro: Não foi possível conectar ao Node. Ele está rodando?")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            time.sleep(1)


if __name__ == "__main__":
    # Simple CLI parsing: --port overrides the port in NODE_URL
    # --host overrides host, --node-url sets full URL, --dry-run only prints resolved URL
    port = None
    host = None
    node_url_arg = None
    dry_run = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--port" and i + 1 < len(args):
            try:
                port = int(args[i + 1])
                i += 2
                continue
            except ValueError:
                print("❌ Erro: --port requer um número válido")
                sys.exit(1)
        if a == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
            continue
        if a == "--node-url" and i + 1 < len(args):
            node_url_arg = args[i + 1]
            i += 2
            continue
        if a == "--dry-run":
            dry_run = True
            i += 1
            continue
        i += 1

    resolved_node_url = NODE_URL
    if node_url_arg:
        resolved_node_url = node_url_arg
    else:
        # Parse existing URL and replace host/port if requested
        try:
            p = urlparse(NODE_URL)
            netloc = p.hostname or 'localhost'
            if host:
                netloc = host
            if port:
                netloc = f"{netloc}:{port}"
            elif p.port:
                netloc = f"{netloc}:{p.port}"
            resolved_node_url = urlunparse((p.scheme or 'http', netloc, p.path or '', '', '', ''))
        except Exception:
            # Fallback simples
            if host and port:
                resolved_node_url = f"http://{host}:{port}"
            elif port:
                resolved_node_url = f"http://localhost:{port}"

    if dry_run:
        print(f"🔎 Dry run — NODE_URL resolvido: {resolved_node_url}")
        sys.exit(0)

    try:
        start_miner(node_url=resolved_node_url)
    except KeyboardInterrupt:
        print("\n🛑 Minerador parado.")
