"""
RAG Pipeline for PolicySight (Phase 4, v3.0)
Chroma-based vector retrieval for section-grounded policy answers.
"""

import re
import os
from typing import Optional
from pydantic import BaseModel

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "chroma_db")
COLLECTION_NAME = "policy_chunks"


class RetrievedChunk(BaseModel):
    content: str
    section: str
    doc_id: str
    score: float


SECTION_HEADERS = [
    "COVERAGE", "EXCLUSIONS", "ENDORSEMENT", "CONDITIONS", "DEFINITIONS",
    "LIABILITY", "COLLISION", "COMPREHENSIVE", "MEDICAL", "UNINSURED",
    "RENTAL", "ROADSIDE", "DUTIES AFTER", "CANCELLATION", "OUR RIGHT TO RECOVER",
    "GENERAL PROVISIONS", "DECLARATIONS", "COVERED AUTO",
]


class PolicyEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:
        return self.model.encode(list(input), show_progress_bar=False).tolist()


def _chunk_policy_text(text: str, max_chars: int = 600) -> list[dict]:
    """
    Split policy text into meaningful chunks by insurance section headers,
    then sub-split large sections by paragraph.
    """
    chunks: list[dict] = []
    lines = text.split("\n")

    current_section = "General"
    current_lines: list[str] = []

    def flush_section():
        if not current_lines:
            return
        para = "\n".join(current_lines).strip()
        if not para:
            return
        if len(para) <= max_chars:
            chunks.append({"text": para, "section": current_section})
        else:
            # sub-split long sections by paragraph
            paragraphs = para.split("\n\n")
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                if len(p) <= max_chars:
                    chunks.append({"text": p, "section": current_section})
                else:
                    # split by sentence
                    sentences = re.split(r"(?<=[.!])\s+", p)
                    buf = ""
                    for s in sentences:
                        if len(buf) + len(s) <= max_chars:
                            buf += " " + s if buf else s
                        else:
                            if buf:
                                chunks.append({"text": buf.strip(), "section": current_section})
                            buf = s
                    if buf:
                        chunks.append({"text": buf.strip(), "section": current_section})
        current_lines.clear()

    for line in lines:
        upper = line.strip().upper()
        # Check if this line starts a new section
        is_header = False
        for header in SECTION_HEADERS:
            if upper.startswith(header) or upper == header:
                is_header = True
                break
        if is_header and current_lines:
            flush_section()
            current_section = line.strip()
            continue
        current_lines.append(line)

    flush_section()
    return chunks


class RagPipeline:
    def __init__(self, persist_dir: str = CHROMA_DIR):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedding_fn = PolicyEmbeddingFunction()

    def _get_collection(self):
        return self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def ingest(self, text: str, doc_id: str) -> int:
        """
        Chunk and index policy text into Chroma.
        Returns the number of chunks indexed.
        """
        collection = self._get_collection()
        chunks = _chunk_policy_text(text)

        # Remove existing chunks for this doc_id
        try:
            existing = collection.get(where={"doc_id": doc_id})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for i, chunk in enumerate(chunks):
            ids.append(f"{doc_id}_chunk_{i}")
            documents.append(chunk["text"])
            metadatas.append({
                "doc_id": doc_id,
                "section": chunk["section"],
                "chunk_index": i,
            })

        if documents:
            collection.add(documents=documents, ids=ids, metadatas=metadatas)

        return len(documents)

    def retrieve(self, query: str, k: int = 5, doc_id: Optional[str] = None) -> list[RetrievedChunk]:
        """
        Retrieve the top-k most relevant chunks for a query.
        Optionally filter by doc_id.
        """
        collection = self._get_collection()

        where_filter = None
        if doc_id:
            where_filter = {"doc_id": doc_id}

        results = collection.query(
            query_texts=[query],
            n_results=k,
            where=where_filter,
        )

        chunks: list[RetrievedChunk] = []
        if not results["ids"] or not results["ids"][0]:
            return chunks

        for i, doc_id_str in enumerate(results["ids"][0]):
            content = results["documents"][0][i] if results["documents"] else ""
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0.0
            score = 1.0 - distance  # cosine distance → similarity

            chunks.append(RetrievedChunk(
                content=content,
                section=meta.get("section", "General"),
                doc_id=meta.get("doc_id", doc_id_str.split("_chunk_")[0]),
                score=score,
            ))

        return chunks

    def count_chunks(self, doc_id: Optional[str] = None) -> int:
        """Count chunks in the collection, optionally filtered by doc_id."""
        collection = self._get_collection()
        where_filter = {"doc_id": doc_id} if doc_id else None
        try:
            return collection.count(where=where_filter)
        except Exception:
            return 0

    def delete_document(self, doc_id: str) -> None:
        """Remove all chunks for a given document."""
        collection = self._get_collection()
        try:
            existing = collection.get(where={"doc_id": doc_id})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass
