from typing import Iterable
import os
from __future__ import annotations
import psycopg
from openai import AsyncOpenAI
from pgvector.psycopg import register_vector_async
class TextChunk:
    chunk_index:int
    content:str
    page_number: int| None= None


class DocumentChunkingService:
    "Goal :Create chunks "


    def __init__(
            self,
            chunk_size:int=500,
            chunk_overlap: int=75,
            embedding_batch_size: int = 100,
            embedding_model="qwen:3b"
    )-> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size")
        self.chunk_size= chunk_size
        self.chunk_overlap=chunk_overlap
        self.embedding_batch_size=embedding_batch_size

    def chunk_text(self, text:str)-> list[TextChunk]:
        words= text.split()
        chunks: list[TextChunk]=[]
        step = self.chunk_size-self.chunk_overlap
        len=len(text)
        i=0

        for i, start in enumerate(range(0,len(text),step)):
            content = " ".join(
            words[start:start + self.chunk_size]
        ).strip()
            if content:
                chunk=TextChunk()
                chunk.chunk_index=i
                chunk.content=content

                chunks.append(chunk)
        return chunks

    async def embed(self, chunks: Iterable[TextChunk]) -> list[list[float]]:
        chunks = list(chunks)
        embeddings: list[list[float]] = []

        for start in range(0, len(chunks), self.embedding_batch_size):
            batch = chunks[start : start + self.embedding_batch_size]
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=[chunk.content for chunk in batch],
            )
            embeddings.extend(item.embedding for item in response.data)

        return embeddings

    async def process_and_store(
            self, document_id: int, extracted_text: str
        ) -> int:
            chunks = self.chunk_text(extracted_text)
            embeddings = await self.embed(chunks)
    
            async with await psycopg.AsyncConnection.connect(
                host="localhost",
                dbname=os.environ.get("POSTGRES_DB"),
                user=os.environ.get("POSTGRES_USER"),
                password=os.environ.get("POSTGRES_PASSWORD"),
            ) as conn:
                await register_vector_async(conn)
                async with conn.cursor() as cur:
                    # Reprocessing replaces the old chunks, so retries do not duplicate data.
                    await cur.execute(
                        "DELETE FROM document_chunks WHERE document_id = %s",
                        (document_id,),
                    )
                    await cur.executemany(
                        """
                        INSERT INTO document_chunks
                            (document_id, chunk_index, content, embedding)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [
                            (document_id, chunk.chunk_index, chunk.content, embedding)
                            for chunk, embedding in zip(chunks, embeddings)
                        ],
                    )
                    await cur.execute(
                        "UPDATE documents SET status = %s, error_message = NULL WHERE id = %s",
                        ("PROCESSED", document_id),
                    )
    
            return len(chunks)
    