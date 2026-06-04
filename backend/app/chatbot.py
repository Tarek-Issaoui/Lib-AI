from typing import Any, Dict, List, Optional

import chromadb
import google.generativeai as genai

from .models import Livre
from .config import settings

SYSTEM_PROMPT = """Tu es l'Assistant Intelligent du Système de Bibliothèque Universitaire iTeam.
Ton ton est professionnel, poli, serviable et accueillant. Tu réponds en français.
Tu dois UNIQUEMENT utiliser les données de la bibliothèque fournies dans le contexte.
Si un livre n'est pas dans les données, indique clairement qu'il n'existe pas dans notre catalogue.
Si un livre est 'emprunté', communique la date de retour prévue si disponible.
Structure tes réponses de manière claire avec des listes formatées.

# EXEMPLES DE RÉPONSES ATTENDUES

User: "Est-ce que le livre avec l'ID 102 existe ?"
Assistant: "Oui, ce livre existe dans la bibliothèque.
- **Titre** : Le Petit Prince
- **Auteur** : Antoine de Saint-Exupéry
- **Statut** : Disponible (3 exemplaires)"

User: "Le roman Les Misérables est-il disponible ?"
Assistant: "Non, ce roman est actuellement emprunté.
- **Titre** : Les Misérables
- **Auteur** : Victor Hugo
- **Statut** : Emprunté
- **Retour prévu le** : 15/03/2026"

User: "Je veux un roman romantique facile à lire."
Assistant: "Bien sûr ! Voici mes recommandations :
1. **Orgueil et Préjugés** - Jane Austen (Disponible)
2. **Jane Eyre** - Charlotte Brontë (Disponible)"

User: "Je cherche un livre de Victor Hugo."
Assistant: "Victor Hugo est dans notre catalogue. Voici ses œuvres disponibles :
1. **Les Misérables** : Emprunté (retour le 15/03/2026)
2. **Notre-Dame de Paris** : Disponible (2 exemplaires)"

# RÈGLES IMPORTANTES
- Réponds UNIQUEMENT avec les livres fournis dans le contexte
- Si aucune information n'est disponible, dis "Ce livre n'existe pas dans notre catalogue"
- Utilise toujours le format avec tirets et listes numérotées
- Sois concis et précis
"""


class LibraryChatbot:
    def __init__(self, persist_directory: str = ".chromadb"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="library_books",
            metadata={"hnsw:space": "cosine"},
        )
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def add_books(self, books: List[Livre]) -> int:
        ids, documents, metadatas = [], [], []
        for book in books:
            if book.id_livre is None:
                continue
            ids.append(str(book.id_livre))
            documents.append(self._build_document_text(book))
            metadatas.append(self._build_metadata(book))
        if not ids:
            return 0
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def add_book(self, book: Livre) -> int:
        if book.id_livre is None:
            return 0
        self.collection.upsert(
            ids=[str(book.id_livre)],
            documents=[self._build_document_text(book)],
            metadatas=[self._build_metadata(book)],
        )
        return 1

    def query_books(self, question: str, n_results: int = 3) -> List[Dict[str, Any]]:
        result = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        return [{"document": doc, "metadata": meta} for doc, meta in zip(documents, metadatas)]

    def answer_question(self, question: str, n_results: int = 3) -> Dict[str, Any]:
        matches = self.query_books(question, n_results=n_results)
        prompt = self._build_prompt(question, matches)
        answer = self._generate_answer(prompt)
        sources = [m["metadata"].get("title", "unknown") for m in matches]
        return {"answer": answer, "sources": sources}

    def _build_metadata(self, book: Livre) -> Dict[str, str]:
        return {
            "title": book.titre,
            "author": book.auteur,
            "year": str(book.annee_publication),
            "status": book.status.value if hasattr(book.status, "value") else str(book.status),
            "category_id": str(book.category_id or ""),
            "category_name": book.category.name if book.category else "",
        }

    def _build_document_text(self, book: Livre) -> str:
        parts = [
            f"Titre: {book.titre}",
            f"Auteur: {book.auteur}",
            f"Année: {book.annee_publication}",
            f"Statut: {book.status.value if hasattr(book.status, 'value') else book.status}",
        ]
        if book.category:
            parts.append(f"Catégorie: {book.category.name}")
        return "\n".join(parts)

    def _build_prompt(self, question: str, matches: List[Dict[str, Any]]) -> str:
        context_block = ""
        if matches:
            context_block = "\n\nContexte — livres de la bibliothèque :\n"
            for idx, match in enumerate(matches, start=1):
                m = match["metadata"]
                context_block += (
                    f"Livre {idx}: {m.get('title', 'inconnu')}\n"
                    f"  Auteur: {m.get('author', 'inconnu')}\n"
                    f"  Année: {m.get('year', 'inconnue')}\n"
                    f"  Statut: {m.get('status', 'inconnu')}\n"
                    f"  Catégorie: {m.get('category_name', 'inconnue')}\n\n"
                )
        return f"{SYSTEM_PROMPT}{context_block}\nQuestion de l'utilisateur: {question}\nRéponse:"

    def _generate_answer(self, prompt: str) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=512),
        )
        return response.text
