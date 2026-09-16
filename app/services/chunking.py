from typing import Iterable
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