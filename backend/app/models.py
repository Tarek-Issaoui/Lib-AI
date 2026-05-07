from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Enum



class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    livres: List["Livre"] = Relationship(back_populates="category")


class Livre(SQLModel, table=True):
    id_livre: Optional[int] = Field(default=None, primary_key=True)
    titre: str = Field(index=True, unique=True)
    auteur: str = Field(index=True)
    annee_publication : int = Field(default = None)
    category_id : Optional[int] =Field(default=None, foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="livres")
    status: str = Field(default="available")

class BookStatus(str, Enum):
    DISPONIBLE = "disponible"
    EMPRUNTE = "emprunte"
    RESERVE = "reserve"