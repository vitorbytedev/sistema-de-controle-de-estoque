from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Produto:
    nome: str
    categoria: str
    quantidade: int
    preco: float
    estoque_minimo: int
    id: Optional[int] = None
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            nome=row["nome"],
            categoria=row["categoria"],
            quantidade=row["quantidade"],
            preco=row["preco"],
            estoque_minimo=row["estoque_minimo"],
            criado_em=row["criado_em"],
            atualizado_em=row["atualizado_em"],
        )


@dataclass
class Movimentacao:
    produto_id: int
    tipo: str  
    quantidade: int
    observacao: Optional[str] = None
    id: Optional[int] = None
    criado_em: Optional[str] = None
    produto_nome: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            produto_id=row["produto_id"],
            tipo=row["tipo"],
            quantidade=row["quantidade"],
            observacao=row["observacao"],
            criado_em=row["criado_em"],
            produto_nome=row["produto_nome"] if "produto_nome" in row.keys() else None,
        )
