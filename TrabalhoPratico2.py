import mmap
import os


SHARED_MEMORY_SIZE = 20 * 8

with open('cotacoes.dat', 'wb') as f:
    f.write(b'\0' * SHARED_MEMORY_SIZE)

shared_memory = mmap.mmap(os.open('cotacoes.dat', os.O_RDWR), SHARED_MEMORY_SIZE)

#Semáforo para sinconizar a escrita e leitura da memória compartilhada
sem = Semaphore(1)


#Criacao do processo servidor
def servidor(sem):
    while True:
        with sem:
            for i in range(20):
                new_value = random.uniform(10, 100)
                shared_memory.seek(i * 8)
                shared_memory.write(struct.pack('d', new_value))
        #Atualiza as cotações a cada 5 seg
        time.sleep(5)

#Cliente que lê as cotações
def corretor(id, sem):
    while True:
        with sem:
            acao_id = random.randint(0, 19)
            shared_memory.seek(acao_id * 8)
            acao_value = struct.unpack('d', shared_memory.read(8))[0]

            print(f'Corretor {id} comprou/vendou ação {acao_id} ao preço de  {acao_value}')

        #Intervalo entre as operações
        time.sleep(random.uniform(1, 3))

#Criação dos processos clientes
for i in range(10):
    p = multiplass.Process(target=corretor, args=(i, sem))
    p.start()

def policial(sem):