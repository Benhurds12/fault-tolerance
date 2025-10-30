# Projeto Fault Tolerance — IMDTravel System

Este repositório contém a implementação da **versão inicial do sistema tolerante a falhas (Unidade 2 – Parte 1)** da disciplina.  
O objetivo é simular uma arquitetura de **microsserviços REST**, desenvolvida em **Python (Flask)**, executando de forma isolada em **containers Docker**.

---

## Visão Geral do Sistema

O sistema é composto por **quatro serviços independentes**, cada um com responsabilidades específicas.  
O serviço principal (**IMDTravel**) orquestra a comunicação entre os demais, simulando o processo de compra de passagens aéreas.

| Serviço | Função | Endpoints |
|----------|--------|-----------|
| **IMDTravel** | Serviço principal que orquestra as requisições e simula a compra da passagem. | `POST /buyTicket` |
| **AirlinesHub** | Gerencia os dados e confirma a venda de voos. | `GET /flight`, `POST /sell` |
| **Exchange** | Retorna taxa de câmbio (USD → BRL), gerada aleatoriamente entre 5 e 6. | `GET /exchange` |
| **Fidelity** | Calcula e registra bônus de fidelidade com base no valor da compra. | `POST /bonus` |

---

## Tecnologias Utilizadas

- **Python 3.10+**  
- **Flask** (para as APIs REST)  
- **Requests** (para comunicação entre serviços)  
- **Docker** e **Docker Compose** (para execução em containers)  

---

## 🐳 Execução com Docker (recomendado)

### 1. Clonar o repositório
```bash
git clone https://github.com/Benhurds12/fault-tolerance.git
cd fault-tolerance
docker-compose up --build -d
```

---

## Fluxo das Requisições

1. **Cliente** → `IMDTravel /buyTicket`  

2. **IMDTravel** → `AirlinesHub /flight` (consulta dados do voo)  

3. **IMDTravel** → `Exchange /exchange` (obtém taxa de câmbio)  

4. **IMDTravel** → `AirlinesHub /sell` (confirma venda e gera ID de transação)  

5. **IMDTravel** → `Fidelity /bonus` (envia bônus ao usuário) 

6. **IMDTravel** → Retorna resposta final ao cliente ✅  
