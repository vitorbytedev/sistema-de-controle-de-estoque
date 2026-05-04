# 📦 Sistema de controle de estoque

Sistema de controle de estoque com backend Python e frontend HTML/CSS/JS.

---

## Estrutura

```
sistema-de-controle-de-estoque/
├── backend/
│   ├── main.py        
│   ├── models.py      
│   └── database.py    
├── frontend/
│   ├── index.html     
│   ├── style.css      
│   └── script.js      
└── README.md
└── .gitignore
```

---

## Requisitos

- Python 3.8+  
- Nenhuma dependência externa — usa apenas stdlib (`sqlite3`, `http.server`, `json`)

---

## Como rodar

### 1. Backend

```bash
cd estoque-system
python backend/main.py
```

Servidor iniciará em **http://localhost:8000**

### 2. Frontend

Abra o arquivo diretamente no browser:

```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html

# Windows
start frontend/index.html
```

> **Atenção:** o browser precisa permitir requisições para `localhost:8000`.  
> Se houver bloqueio de CORS ao abrir como `file://`, sirva com:
> ```bash
> python -m http.server 3000 --directory frontend
> # Acesse http://localhost:3000
> ```

---

## API REST

| Método | Rota                            | Descrição                   |
|--------|---------------------------------|-----------------------------|
| GET    | `/api/dashboard`                | Métricas gerais             |
| GET    | `/api/produtos`                 | Listar produtos             |
| GET    | `/api/produtos?busca=X`         | Buscar por nome             |
| GET    | `/api/produtos?categoria=X`     | Filtrar por categoria       |
| POST   | `/api/produtos`                 | Criar produto               |
| PUT    | `/api/produtos/:id`             | Atualizar produto           |
| DELETE | `/api/produtos/:id`             | Remover produto             |
| GET    | `/api/movimentacoes`            | Histórico completo          |
| GET    | `/api/produtos/:id/movimentacoes` | Movimentações do produto  |
| POST   | `/api/movimentacoes`            | Registrar entrada/saída     |

### Exemplo — criar produto

```bash
curl -X POST http://localhost:8000/api/produtos \
  -H "Content-Type: application/json" \
  -d '{"nome":"Cabo HDMI","categoria":"Periféricos","quantidade":50,"preco":29.90,"estoque_minimo":10}'
```

### Exemplo — registrar entrada

```bash
curl -X POST http://localhost:8000/api/movimentacoes \
  -H "Content-Type: application/json" \
  -d '{"produto_id":1,"tipo":"entrada","quantidade":10,"observacao":"Reposição mensal"}'
```

---

## Funcionalidades

- CRUD completo de produtos
- Registro de entradas e saídas com histórico
- Alertas de estoque baixo / zerado
- Dashboard com valor total, categorias e movimentações da semana
- Filtro e busca em tempo real
- Banco SQLite local (sem configuração)
- Dados de demonstração (seed automático)

---

## Banco de dados

O arquivo `backend/estoque.db` é criado automaticamente na primeira execução com 8 produtos de demonstração. Para resetar, basta deletar o arquivo e reiniciar o servidor.
