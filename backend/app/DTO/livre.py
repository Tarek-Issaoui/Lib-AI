from typing import Optional
from sqlmodel import SQLModel
from app.models import BookStatus


class LivreOut(SQLModel):
    id_livre: int
    titre: str
    auteur: str
    annee_publication: int
    status: BookStatus
    category_id: Optional[int]


class LivreWithCategoryOut(LivreOut):
    category_name: str
