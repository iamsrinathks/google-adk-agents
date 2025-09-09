import os
import pg8000
from typing import Any, Dict, List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google.adk.tools import LongRunningFunctionTool
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


class GuidelineConsultantTool:
    """
    Tool to insert and retrieve guideline snippets from AlloyDB using pg8000 + pgvector.
    Supports chunking and metadata (category, tags).
    """

    def __init__(self):
        # DB connection params
        self.db_user = os.getenv("ALLOYDB_USER")
        self.db_pass = os.getenv("ALLOYDB_PASS")
        self.db_name = os.getenv("ALLOYDB_NAME")
        self.db_host = os.getenv("ALLOYDB_HOST")
        self.db_port = int(os.getenv("ALLOYDB_PORT"))
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION")
        self.cluster = os.getenv("ALLOYDB_CLUSTER")
        self.instance = os.getenv("ALLOYDB_INSTANCE")

        # Embedding model — force 768‑dim output
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001"
        )
        self.embedding_dim = 768  # matches output_dimensionality

        # Ensure schema exists on init
        self._ensure_schema()

    def _connect(self):
        """Create a pg8000 connection."""
        return pg8000.connect(
            user=self.db_user,
            password=self.db_pass,
            database=self.db_name,
            host=self.db_host,
            port=self.db_port,
        )

    def _ensure_schema(self):
        """Ensure table and vector index exist."""
        try:
            conn = self._connect()
            cur = conn.cursor()

            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Ensure table exists with metadata columns
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS product_guidelines (
                id BIGSERIAL PRIMARY KEY,
                document_name TEXT,
                chunk_index INT NOT NULL,
                category TEXT,
                tags TEXT[],
                text_content TEXT,
                embedding vector({self.embedding_dim})
            );
            """)

            # Ensure vector index exists
            cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_indexes
                    WHERE tablename = 'product_guidelines'
                      AND indexname = 'product_guidelines_embedding_idx'
                ) THEN
                    CREATE INDEX product_guidelines_embedding_idx
                    ON product_guidelines
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                END IF;
            END$$;
            """)

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"⚠️ Schema setup failed: {e}")

    def _embed_text(self, text: str) -> List[float]:
        """Get embedding vector for a single text input."""
        return self.embedding_model.embed_query(
            text,
            output_dimensionality=self.embedding_dim
        )

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in a single API call (faster)."""
        return self.embedding_model.embed_documents(
            texts,
            output_dimensionality=self.embedding_dim
        )

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def add_document(self, document_name: str, text_content: str,
                     category: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Embed and insert a document in chunks with metadata."""
        try:
            chunks = self._chunk_text(text_content)
            embeddings = self._embed_texts(chunks)

            conn = self._connect()
            cur = conn.cursor()

            inserted_ids = []
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                vector_str = "[" + ",".join(str(x) for x in emb) + "]"
                cur.execute(
                    """
                    INSERT INTO product_guidelines
                    (document_name, chunk_index, category, tags, text_content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
                    RETURNING id;
                    """,
                    (document_name, idx, category, tags, chunk, vector_str),
                )
                inserted_ids.append(cur.fetchone()[0])

            conn.commit()
            cur.close()
            conn.close()

            return {"status": "success", "inserted_ids": inserted_ids}

        except Exception as e:
            return {"error": str(e)}

    def execute(self, query_text: str, top_k: int = 4,
                category: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute similarity search with optional metadata filters."""
        try:
            query_embedding = self._embed_text(query_text)
            vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            conn = self._connect()
            cur = conn.cursor()

            sql = """
            SELECT id, document_name, chunk_index, category, tags, text_content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM product_guidelines
            WHERE 1=1
            """
            params = [vector_str]

            if category:
                sql += " AND category = %s"
                params.append(category)
            if tags:
                sql += " AND tags && %s"  # overlap operator for arrays
                params.append(tags)

            sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([vector_str, top_k])

            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

            cur.close()
            conn.close()

            snippets = [
                {
                    "id": row[0],
                    "document_name": row[1],
                    "chunk_index": row[2],
                    "category": row[3],
                    "tags": row[4],
                    "text_content": row[5],
                    "similarity": float(row[6]),
                }
                for row in rows
            ]

            return {"guideline_snippets": snippets}

        except Exception as e:
            return {"error": str(e)}


# Helper for direct calls
def search_documents_in_alloydb(query: str, k: int = 4,
                                category: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    tool = GuidelineConsultantTool()
    results = tool.execute(query_text=query, top_k=k, category=category, tags=tags)
    snippets = results.get("guideline_snippets", [])
    if not snippets:
        return "No relevant guidelines found."
    return "\n\n".join(s["text_content"] for s in snippets)


# Register with ADK
guideline_search_tool = LongRunningFunctionTool(func=search_documents_in_alloydb)

# if __name__ == "__main__":
#     tool = GuidelineConsultantTool()

#     # Example: Add a sample document with metadata
#     doc = {
#         "document_name": "Sample Guideline",
#         "text_content": "Always encrypt sensitive data at rest and in transit. Use strong encryption algorithms...",
#         "category": "Security",
#         "tags": ["encryption", "data-protection"]
#     }
#     print("Inserting document:", tool.add_document(**doc))

#     # Example: Search with category filter
#     query = "How to protect sensitive information?"
#     print("Search results:", tool.execute(query_text=query, top_k=3, category="Security"))
