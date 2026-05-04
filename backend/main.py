"""
Estoque System - Backend API
Rode com: python backend/main.py
API disponível em: http://localhost:8000
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_connection
from models import Produto, Movimentacao

PORT = 8000


def json_response(handler, status: int, data):
    body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(length)
    return json.loads(raw) if raw else {}


def get_produtos(params: dict):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM produtos"
    args = []
    filters = []
    if "categoria" in params:
        filters.append("categoria = ?")
        args.append(params["categoria"][0])
    if "busca" in params:
        filters.append("nome LIKE ?")
        args.append(f"%{params['busca'][0]}%")
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY nome"
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return [Produto.from_row(r).to_dict() for r in rows]


def create_produto(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO produtos (nome, categoria, quantidade, preco, estoque_minimo) VALUES (?,?,?,?,?)",
        (data["nome"], data["categoria"], data.get("quantidade", 0),
         data.get("preco", 0.0), data.get("estoque_minimo", 5))
    )
    conn.commit()
    produto_id = cur.lastrowid
    cur.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cur.fetchone()
    conn.close()
    return Produto.from_row(row).to_dict()


def update_produto(produto_id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE produtos SET nome=?, categoria=?, quantidade=?, preco=?, estoque_minimo=?,
           atualizado_em=CURRENT_TIMESTAMP WHERE id=?""",
        (data["nome"], data["categoria"], data["quantidade"],
         data["preco"], data["estoque_minimo"], produto_id)
    )
    conn.commit()
    cur.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return Produto.from_row(row).to_dict()


def delete_produto(produto_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_movimentacoes(produto_id: int = None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT m.*, p.nome as produto_nome
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
    """
    args = []
    if produto_id:
        query += " WHERE m.produto_id = ?"
        args.append(produto_id)
    query += " ORDER BY m.criado_em DESC LIMIT 100"
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return [Movimentacao.from_row(r).to_dict() for r in rows]


def create_movimentacao(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT quantidade FROM produtos WHERE id = ?", (data["produto_id"],))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None, "Produto não encontrado"

    qtd_atual = row["quantidade"]
    tipo = data["tipo"]
    qtd = int(data["quantidade"])

    if tipo == "saida" and qtd > qtd_atual:
        conn.close()
        return None, f"Estoque insuficiente. Disponível: {qtd_atual}"

    nova_qtd = qtd_atual + qtd if tipo == "entrada" else qtd_atual - qtd
    cur.execute(
        "UPDATE produtos SET quantidade=?, atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
        (nova_qtd, data["produto_id"])
    )
    cur.execute(
        "INSERT INTO movimentacoes (produto_id, tipo, quantidade, observacao) VALUES (?,?,?,?)",
        (data["produto_id"], tipo, qtd, data.get("observacao"))
    )
    conn.commit()
    mov_id = cur.lastrowid
    cur.execute(
        "SELECT m.*, p.nome as produto_nome FROM movimentacoes m JOIN produtos p ON p.id=m.produto_id WHERE m.id=?",
        (mov_id,)
    )
    row = cur.fetchone()
    conn.close()
    return Movimentacao.from_row(row).to_dict(), None



def get_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM produtos")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as baixo FROM produtos WHERE quantidade <= estoque_minimo")
    estoque_baixo = cur.fetchone()["baixo"]
    cur.execute("SELECT SUM(quantidade * preco) as valor FROM produtos")
    valor_total = cur.fetchone()["valor"] or 0
    cur.execute("""
        SELECT categoria, COUNT(*) as qtd, SUM(quantidade) as total_itens
        FROM produtos GROUP BY categoria ORDER BY qtd DESC
    """)
    categorias = [dict(r) for r in cur.fetchall()]
    cur.execute("""
        SELECT m.tipo, COUNT(*) as total
        FROM movimentacoes m
        WHERE date(m.criado_em) >= date('now', '-7 days')
        GROUP BY m.tipo
    """)
    movs = {r["tipo"]: r["total"] for r in cur.fetchall()}
    conn.close()
    return {
        "total_produtos": total,
        "estoque_baixo": estoque_baixo,
        "valor_total": round(valor_total, 2),
        "categorias": categorias,
        "movimentacoes_semana": movs,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "/api/dashboard":
            json_response(self, 200, get_dashboard())

        elif path == "/api/produtos":
            json_response(self, 200, get_produtos(params))

        elif path.startswith("/api/produtos/") and "/movimentacoes" in path:
            pid = int(path.split("/")[3])
            json_response(self, 200, get_movimentacoes(pid))

        elif path == "/api/movimentacoes":
            json_response(self, 200, get_movimentacoes())

        else:
            json_response(self, 404, {"erro": "Rota não encontrada"})

    def do_POST(self):
        path = self.path.rstrip("/")
        data = read_body(self)

        if path == "/api/produtos":
            try:
                produto = create_produto(data)
                json_response(self, 201, produto)
            except KeyError as e:
                json_response(self, 400, {"erro": f"Campo obrigatório: {e}"})

        elif path == "/api/movimentacoes":
            resultado, erro = create_movimentacao(data)
            if erro:
                json_response(self, 400, {"erro": erro})
            else:
                json_response(self, 201, resultado)

        else:
            json_response(self, 404, {"erro": "Rota não encontrada"})

    def do_PUT(self):
        path = self.path.rstrip("/")
        parts = path.split("/")

        if len(parts) == 4 and parts[2] == "produtos":
            pid = int(parts[3])
            data = read_body(self)
            resultado = update_produto(pid, data)
            if resultado:
                json_response(self, 200, resultado)
            else:
                json_response(self, 404, {"erro": "Produto não encontrado"})
        else:
            json_response(self, 404, {"erro": "Rota não encontrada"})

    def do_DELETE(self):
        path = self.path.rstrip("/")
        parts = path.split("/")

        if len(parts) == 4 and parts[2] == "produtos":
            pid = int(parts[3])
            if delete_produto(pid):
                json_response(self, 200, {"mensagem": "Produto removido"})
            else:
                json_response(self, 404, {"erro": "Produto não encontrado"})
        else:
            json_response(self, 404, {"erro": "Rota não encontrada"})


if __name__ == "__main__":
    init_db()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f" Servidor rodando em http://localhost:{PORT}")
    print(f" Banco de dados: {os.path.abspath('backend/estoque.db')}")
    print("     Pressione Ctrl+C para encerrar\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Servidor encerrado.")
