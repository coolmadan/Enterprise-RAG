from fastapi import APIRouter,HTTPException
from fastapi import status
import fitz
import psycopg, os
from dotenv import load_dotenv
load_dotenv()
router = APIRouter()

host='localhost'
Database_name=os.environ.get("POSTGRES_DB")
Database_user=os.environ.get("POSTGRES_USER")
Database_password=os.environ.get("POSTGRES_PASSWORD")
#connect to db get the document extract the content and return the content to the user
@router.post("/documents/{id}/process")
async def process_document(id: int):
    conn=psycopg.connect(
        host=host,
        dbname=Database_name,
        user=Database_user,
        password=Database_password
    )
    with conn.cursor() as curr:
        curr.execute("SELECT file_path from documents where id=%s",(id,))
        result=curr.fetchone()
        if result :
            conn.close()
            file_path=result[0]
        else :
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST,detail='File not present in database')
    doc= fitz.open(file_path)
    extracted_text=""
    for page in doc:
        extracted_text+=page.get_text()

    doc.close()
    return {
    "content": extracted_text
}
