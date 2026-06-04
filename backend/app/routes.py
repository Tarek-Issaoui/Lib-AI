from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from typing import List

from .models import Livre, Category
from .database import get_session
from .DTO.livre import LivreWithCategoryOut
from .DTO.chatbot import ChatRequest, ChatResponse
from .chatbot import LibraryChatbot

router = APIRouter()
chatbot = LibraryChatbot()


@router.get("/livres/", response_model=List[Livre])
def get_livres(session: Session = Depends(get_session)):
    return session.exec(select(Livre)).all()


@router.get("/livres/{livre_id}/", response_model=LivreWithCategoryOut)
def get_livre(livre_id: int, session: Session = Depends(get_session)):
    statement = select(Livre, Category).join(Category).where(Livre.id_livre == livre_id)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="livre non trouvé")
    livre, category = result
    livre_to_dict = livre.model_dump()
    livre_to_dict["category_name"] = category.name
    return livre_to_dict


@router.post("/livres/", response_model=Livre)
def ajouter_livre(new_livre: Livre, session: Session = Depends(get_session)):
    session.add(new_livre)
    session.commit()
    session.refresh(new_livre)
    # reload with category relationship for indexing
    statement = select(Livre).where(Livre.id_livre == new_livre.id_livre).options(
        selectinload(Livre.category)
    )
    livre_with_category = session.exec(statement).first()
    chatbot.add_book(livre_with_category or new_livre)
    return new_livre


@router.post("/categories/", response_model=Category)
def ajouter_category(new_category: Category, session: Session = Depends(get_session)):
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    return new_category


@router.post("/chatbot/index/")
def rebuild_chat_index(session: Session = Depends(get_session)):
    statement = select(Livre).options(selectinload(Livre.category))
    livres = session.exec(statement).all()
    indexed = chatbot.add_books(livres)
    return {"status": "ok", "indexed_books": indexed}


@router.post("/chatbot/query/", response_model=ChatResponse)
def chat_with_library(query: ChatRequest):
    answer_data = chatbot.answer_question(query.question)
    return ChatResponse(answer=answer_data["answer"], sources=answer_data["sources"])
