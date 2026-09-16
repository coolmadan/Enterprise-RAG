class TextChunk:
    chunk_index:int
    content:str
    page_number: int| None= None


class DocumentChunkingService:
    "Goal :Create chunks "


    def __init__(
            self,
            chunk_size:int=500,
            chunk_overlap: int=75
    )-> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size")
        self.chunk_size= chunk_size
        self.chunk_overlap=chunk_overlap

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