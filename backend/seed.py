import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import Category, Livre, BookStatus
from app.chatbot import LibraryChatbot

CATEGORIES = [
    {"name": "Roman", "description": "Fiction narrative longue"},
    {"name": "Science", "description": "Ouvrages scientifiques et techniques"},
    {"name": "Histoire", "description": "Livres d'histoire et de civilisations"},
    {"name": "Informatique", "description": "Programmation, réseaux et systèmes"},
    {"name": "Philosophie", "description": "Pensée, éthique et logique"},
]

BOOKS = [
    # Romans
    {"titre": "Les Misérables", "auteur": "Victor Hugo", "annee_publication": 1862, "status": BookStatus.EMPRUNTE, "category": "Roman"},
    {"titre": "Notre-Dame de Paris", "auteur": "Victor Hugo", "annee_publication": 1831, "status": BookStatus.DISPONIBLE, "category": "Roman"},
    {"titre": "Le Petit Prince", "auteur": "Antoine de Saint-Exupéry", "annee_publication": 1943, "status": BookStatus.DISPONIBLE, "category": "Roman"},
    {"titre": "Orgueil et Préjugés", "auteur": "Jane Austen", "annee_publication": 1813, "status": BookStatus.DISPONIBLE, "category": "Roman"},
    {"titre": "Jane Eyre", "auteur": "Charlotte Brontë", "annee_publication": 1847, "status": BookStatus.DISPONIBLE, "category": "Roman"},
    {"titre": "Madame Bovary", "auteur": "Gustave Flaubert", "annee_publication": 1857, "status": BookStatus.RESERVE, "category": "Roman"},
    {"titre": "L'Étranger", "auteur": "Albert Camus", "annee_publication": 1942, "status": BookStatus.DISPONIBLE, "category": "Roman"},
    # Sciences
    {"titre": "Une brève histoire du temps", "auteur": "Stephen Hawking", "annee_publication": 1988, "status": BookStatus.DISPONIBLE, "category": "Science"},
    {"titre": "Le Gène égoïste", "auteur": "Richard Dawkins", "annee_publication": 1976, "status": BookStatus.EMPRUNTE, "category": "Science"},
    {"titre": "La Physique des particules", "auteur": "Brian Cox", "annee_publication": 2011, "status": BookStatus.DISPONIBLE, "category": "Science"},
    # Histoire
    {"titre": "Sapiens", "auteur": "Yuval Noah Harari", "annee_publication": 2011, "status": BookStatus.DISPONIBLE, "category": "Histoire"},
    {"titre": "Homo Deus", "auteur": "Yuval Noah Harari", "annee_publication": 2015, "status": BookStatus.RESERVE, "category": "Histoire"},
    {"titre": "Le Monde d'hier", "auteur": "Stefan Zweig", "annee_publication": 1942, "status": BookStatus.DISPONIBLE, "category": "Histoire"},
    # Informatique
    {"titre": "Clean Code", "auteur": "Robert C. Martin", "annee_publication": 2008, "status": BookStatus.DISPONIBLE, "category": "Informatique"},
    {"titre": "The Pragmatic Programmer", "auteur": "David Thomas", "annee_publication": 1999, "status": BookStatus.EMPRUNTE, "category": "Informatique"},
    {"titre": "Introduction aux algorithmes", "auteur": "Thomas H. Cormen", "annee_publication": 2009, "status": BookStatus.DISPONIBLE, "category": "Informatique"},
    {"titre": "Design Patterns", "auteur": "Gang of Four", "annee_publication": 1994, "status": BookStatus.DISPONIBLE, "category": "Informatique"},
    # Philosophie
    {"titre": "Le Monde comme volonté et représentation", "auteur": "Arthur Schopenhauer", "annee_publication": 1818, "status": BookStatus.DISPONIBLE, "category": "Philosophie"},
    {"titre": "Ainsi parlait Zarathoustra", "auteur": "Friedrich Nietzsche", "annee_publication": 1883, "status": BookStatus.DISPONIBLE, "category": "Philosophie"},
    {"titre": "Critique de la raison pure", "auteur": "Emmanuel Kant", "annee_publication": 1781, "status": BookStatus.RESERVE, "category": "Philosophie"},
]


def seed():
    with Session(engine) as session:
        # Insert categories
        category_map = {}
        for cat_data in CATEGORIES:
            existing = session.exec(select(Category).where(Category.name == cat_data["name"])).first()
            if existing:
                category_map[existing.name] = existing
            else:
                cat = Category(**cat_data)
                session.add(cat)
                session.flush()
                category_map[cat.name] = cat

        # Insert books
        books_added = []
        for book_data in BOOKS:
            category_name = book_data.pop("category")
            cat = category_map[category_name]

            existing = session.exec(select(Livre).where(Livre.titre == book_data["titre"])).first()
            if existing:
                print(f"  [skip] {book_data['titre']} already exists")
                book_data["category"] = category_name
                continue

            livre = Livre(**book_data, category_id=cat.id, category=cat)
            session.add(livre)
            session.flush()
            books_added.append(livre)
            book_data["category"] = category_name  # restore for idempotency logging

        session.commit()
        for book in books_added:
            session.refresh(book)

        print(f"[OK] {len(CATEGORIES)} categories, {len(books_added)} livres inseres.")

        # Index into ChromaDB
        chatbot = LibraryChatbot()
        all_books = session.exec(select(Livre)).all()
        # attach category objects for indexing
        for book in all_books:
            _ = book.category  # trigger lazy load within session
        indexed = chatbot.add_books(all_books)
        print(f"[OK] {indexed} livres indexes dans ChromaDB.")


if __name__ == "__main__":
    seed()
