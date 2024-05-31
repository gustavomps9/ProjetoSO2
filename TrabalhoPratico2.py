import mmap
import os
import struct
import random
import time
import multiprocessing
from multiprocessing import Semaphore, Process, Manager

# Lista de empresas do PSI-20
empresas = [
    "Altri", "Banco Comercial Português", "Corticeira Amorim", "CTT Correios de Portugal",
    "EDP Renováveis", "Energias de Portugal", "Galp Energia", "Ibersol",
    "Jerónimo Martins", "Mota-Engil", "NOS", "Novabase",
    "Pharol", "Redes Energéticas Nacionais", "Semapa", "Sonae",
    "Sonae Capital", "The Navigator Company"
]

# Defina o tamanho da memória compartilhada (18 ações, cada uma com um double de 8 bytes)
SHARED_MEMORY_SIZE = len(empresas) * 8

# Caminho absoluto para o arquivo de cotações
cotacoes_path = os.path.abspath('cotacoes.dat')

# Criação de um arquivo para memória compartilhada
with open(cotacoes_path, 'wb') as f:
    f.write(b'\0' * SHARED_MEMORY_SIZE)

# Mapeamento do arquivo em memória
shared_memory = mmap.mmap(os.open(cotacoes_path, os.O_RDWR), SHARED_MEMORY_SIZE)

# Semáforo para sincronização de acesso à memória compartilhada
sem = Semaphore(1)

# Valores de referência inicial para cada ação
valor_referencia = [round(random.uniform(10, 100), 2) for _ in empresas]

# Inicialização das cotações com os valores de referência
with sem:
    for i, valor in enumerate(valor_referencia):
        shared_memory.seek(i * 8)
        shared_memory.write(struct.pack('d', valor))

# Lista para armazenar ações suspensas
acoes_suspensas = Manager().list([False] * len(empresas))

# Função do Servidor (Bolsa de Valores)
def servidor(sem, acoes_suspensas):
    while True:
        with sem:
            with open('log_servidor.txt', 'a') as log_servidor:
                for i, empresa in enumerate(empresas):
                    if not acoes_suspensas[i]:
                        new_value = round(random.uniform(10, 100), 2)
                        shared_memory.seek(i * 8)
                        shared_memory.write(struct.pack('d', new_value))
                        log_servidor.write(f'Atualização de ação {empresa}: {new_value:.2f}\n')
        # Exibir as cotações
        with sem:
            print("Cotações atuais das ações:")
            for i, empresa in enumerate(empresas):
                shared_memory.seek(i * 8)
                valor_acao = struct.unpack('d', shared_memory.read(8))[0]
                print(f"{empresa}: {valor_acao:.2f}")
        # Atualiza as cotações a cada 5 segundos
        time.sleep(5)

# Função dos Corretores
def corretor(id, sem, acoes_suspensas):
    while True:
        with sem:
            acao_id = random.randint(0, len(empresas) - 1)
            if not acoes_suspensas[acao_id]:
                shared_memory.seek(acao_id * 8)
                acao_value = struct.unpack('d', shared_memory.read(8))[0]
                # Simulação de compra e venda de ações
                operacao = 'compra' ou 'venda'
                empresa = empresas[acao_id]
                valor_operacao = round(acao_value + random.uniform(-5, 5), 2)
                print(f'Corretor {id} {operacao} ação {empresa} ao preço de {valor_operacao:.2f} euros')
                with open(f'log_corretor_{id}.txt', 'a') as log_corretor:
                    log_corretor.write(f'{operacao} ação {empresa}: {valor_operacao:.2f} euros\n')
        # Intervalo entre as operações
        time.sleep(random.uniform(1, 3))

# Função do Policia da Bolsa
def policia(sem, acoes_suspensas):
    while True:
        with sem:
            with open('log_policia.txt', 'a') as log_policia:
                for i, empresa in enumerate(empresas):
                    shared_memory.seek(i * 8)
                    valor_acao = struct.unpack('d', shared_memory.read(8))[0]
                    variacao = abs(valor_acao - valor_referencia[i]) / valor_referencia[i]
                    if variacao > 0.25:
                        log_policia.write(f'Negociação suspensa para ação {empresa} devido a variação de {variacao * 100:.2f}%\n')
                        # Suspende a ação
                        acoes_suspensas[i] = True
                        # Reseta o valor da ação para o valor de referência
                        shared_memory.seek(i * 8)
                        shared_memory.write(struct.pack('d', valor_referencia[i]))
                    elif acoes_suspensas[i]:
                        log_policia.write(f'Negociação retomada para ação {empresa}\n')
                        acoes_suspensas[i] = False
        time.sleep(10)  # Verifica variações a cada 10 segundos

# Criação dos Processos
if __name__ == '__main__':
    # Processo servidor
    servidor_proc = Process(target=servidor, args=(sem, acoes_suspensas))
    servidor_proc.start()

    # Processos clientes (corretores)
    for i in range(10):
        corretor_proc = Process(target=corretor, args=(i, sem, acoes_suspensas))
        corretor_proc.start()

    # Processo policia
    policia_proc = Process(target=policia, args=(sem, acoes_suspensas))
    policia_proc.start()

    # Aguardar processos
    servidor_proc.join()
    policia_proc.join()
    for proc in multiprocessing.active_children():
        proc.join()
