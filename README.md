# Projeto Fault Tolerance — IMDTravel System

Este repositório contém a implementação da **versão inicial do sistema tolerante a falhas (Unidade 2 – Parte 1)** da disciplina.  
O objetivo é simular uma arquitetura de **microsserviços REST**, desenvolvida em **Python (Flask)**, executando de forma isolada em **containers Docker**.

---

## Visão Geral do Sistema

O sistema é composto por **quatro serviços independentes**, cada um com responsabilidades específicas.  
O serviço principal (**IMDTravel**) ministra a comunicação entre os demais, simulando o processo de compra de passagens aéreas.

| Serviço | Função | Endpoints |
|----------|--------|-----------|
| **IMDTravel** | Serviço principal que orquestra as requisições e simula a compra da passagem. | `POST /buyTicket` |
| **AirlinesHub** | Gerencia os dados e confirma a venda de voos. | `GET /flight`, `POST /sell` |
| **Exchange** | Retorna taxa de câmbio (USD → BRL), gerada aleatoriamente entre 5 e 6. | `GET /convert` |
| **Fidelity** | Calcula e registra bônus de fidelidade com base no valor da compra. | `POST /bonus` |

---
## Grupo
- **Elon Arkell Freire Bezerra**
- **Jose Ben Hur Nascimento de Oliveira** 
- **Luís Henrique Melo Scalabrin**

---

## Tecnologias Utilizadas

- **Python 3.10+**  
- **Flask** (para as APIs REST)  
- **Requests** (para comunicação entre serviços)  
- **Docker** e **Docker Compose** (para execução em containers)  

---

## Execução com Docker (recomendado)

### 1. Clonar o repositório
```bash
git clone https://github.com/Benhurds12/fault-tolerance.git
```
```bash
cd fault-tolerance
```
```bash
docker-compose up --build -d
```

---

## Fluxo das Requisições

1. **Cliente** → `IMDTravel /buyTicket`  

2. **IMDTravel** → `AirlinesHub /flight` (consulta dados do voo)  

3. **IMDTravel** → `Exchange /convert` (obtém taxa de câmbio)  

4. **IMDTravel** → `AirlinesHub /sell` (confirma venda e gera ID de transação)  

5. **IMDTravel** → `Fidelity /bonus` (envia bônus ao usuário) 

6. **IMDTravel** → Retorna resposta final ao cliente

## Respectivas portas das Requisições

1. `/buyTicket` → http://localhost:5000/buyTicket (Content-Type) (application/json) {"flight": "AA123","day": "2025-10-30","user": "example","ft": "true"}
2. `/flight` → http://localhost:5001/flight?flight=AA123&day=2025-10-30 (com parâmetro pro header)
3. `/convert` → http://localhost:5002/convert?convert (sem parâmetros)
4. `/sell` → http://localhost:5001/sell (Content-Type) (application/json) {"flight": "AA123","day": "2025-10-30"}
5. `/bonus` → http://localhost:5003/bonus (Content-Type) (application/json) {"user": "name","amount": 200}

## Execução do K6 para testes

1. `cd k6` → Abrir a pasta do k6
2. `k6 run compare_ft.js` → Compara comportamento **FT=True vs FT=False**. Mostra a diferença real de disponibilidade e resiliência.
3. `k6 run load_test.js` → Executa um **load test gradual**, aumentando usuários aos poucos para medir estabilidade.
4. `k6 run stress_test.js` → Executa um **stress test extremo**, aplicando picos de carga para encontrar limites e gargalos.
5. `k6 run -e FT=true test_graceful.js` Executa o teste de latência com a Tolerância a Falhas Ativada. Valida a estratégia de Fail Fast, verificando se o sistema aborta conexões lentas dentro do limite de segurança (~2s).
6. `k6 run -e FT=false test_graceful.js` Executa o teste de latência com a Tolerância a Falhas Desativada. Simula um cenário de degradação onde o sistema fica bloqueado pela lentidão do serviço externo (~5s), comprovando a falta de resiliência.


