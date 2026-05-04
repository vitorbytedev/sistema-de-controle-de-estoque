import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "estoque.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            preco REAL NOT NULL DEFAULT 0.0,
            estoque_minimo INTEGER NOT NULL DEFAULT 5,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
            quantidade INTEGER NOT NULL,
            observacao TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        seed = [
            ("Notebook Dell", "Eletrônicos", 12, 3500.00, 3),
            ("Mouse Logitech", "Periféricos", 45, 89.90, 10),
            ("Teclado Mecânico", "Periféricos", 8, 259.00, 5),
            ("Monitor 24\"", "Eletrônicos", 6, 1200.00, 2),
            ("Cadeira Gamer", "Mobiliário", 3, 899.00, 2),
            ("Headset Sony", "Periféricos", 20, 349.90, 5),
            ("Webcam HD", "Periféricos", 2, 189.00, 4),
            ("SSD 1TB", "Componentes", 30, 420.00, 8),
        ]
        cursor.executemany(
            "INSERT INTO produtos (nome, categoria, quantidade, preco, estoque_minimo) VALUES (?,?,?,?,?)",
            seed
        )
    conn.commit()
    conn.close()
