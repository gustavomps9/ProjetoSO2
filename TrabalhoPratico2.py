import mmap
import os
import struct
import random
import time
import multiprocessing
from multiprocessing import Semaphore, Process

# Tamanho do segmento de memória para guardar 20 cotações de ações
# 20 ações, cada uma com um valor double (8 bytes)
SHARED_MEMORY_SIZE = 20 * 8

# Criação de um ficheiro para memória partilhada
with open('cotacoes.dat', 'wb') as f:
    f.write(b'\0' * SHARED_MEMORY_SIZE)

# Mapeamento do ficheiro em memória
shared_memory = mmap.mmap(os.open('cotacoes.dat', os.O_RDWR), SHARED_MEMORY_SIZE)

#Semáforo para sinconizar a escrita e leitura da memória compartilhada
sem = Semaphore(1)


#Criacao do processo servidor
#Função do servidor
def servidor(sem):
    while True:
        with sem:
            with open('log_server.txt', 'a') as log_servidor:
                for i in range(20):
                    new_value = random.uniform(10, 100)
                    shared_memory.seek(i * 8)
                    shared_memory.write(struct.pack('d', new_value))
                    log_servidor.write(f'Ação {i} atualizada para {new_value}\n')
        #Atualiza as cotações a cada 5 seg
        time.sleep(5)


#Cliente que lê as cotações
#Função dos corretores
def corretor(id, sem):
    while True:
        with sem:
            acao_id = random.randint(0, 19)
            shared_memory.seek(acao_id * 8)
            acao_value = struct.unpack('d', shared_memory.read(8))[0]

            #Simlula a compra/venda de ações
            operacao = 'compra' if random.random() > 0.5 else 'venda'
            print(f'Corretor {id} {operacao} ação {acao_id} ao preço de {acao_value}')
            with open(f'log_corretor{id}.txt', 'a') as log_corretor:
                log_corretor.write(f'{operacao} ação {acao_id} ao preço de {acao_value}\n')

        #Intervalo entre as operações
        time.sleep(random.uniform(1, 3))
