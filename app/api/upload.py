from fastapi import status
from fastapi import UploadFile,File
from fastapi import APIRouter,HTTPException
from hashlib import sha256
from dotenv import load_dotenv
load_dotenv()
import psycopg,os
router = APIRouter()

@router.post("/upload-file")
async def upload_file(file:UploadFile = File(..., description="Upload a file")):
    if file.content_type!="application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")
    content_bytes= await file.read()
    bits= sha256(content_bytes)#256 bits of content 
    hex_hash= bits.hexdigest()#convert to hex
    #hex charachters are 4 bits each, so 256 bits will be represented by 64 hex characters and 2 hex characters are used to represent 1 byte, so 64 hex characters will be used to represent 32 bytes of content
    conn= psycopg.connect(
        host="localhost",
        dbname=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD")
    )
    with conn.cursor() as curr:
        curr.execute("Select id from documents where content_hash=%s",(hex_hash,))
        result= curr.fetchone()
        if result:
            conn.close()
            return {"message": "File already exists in the database", "document_id": result[0],}
    file_path=f"upload/{hex_hash}.pdf"
    with open(file_path, "wb") as f:
        f.write(content_bytes)
    with conn.cursor() as curr:
        try:
            curr.execute("Insert into documents (filename,content_hash,file_path,status) values (%s, %s, %s, %s)", (file.filename, hex_hash, file_path, "UPLOADED"))
        except Exception as e:
            print(f"Error occurred while inserting document: {e}")
    conn.commit()
    conn.close()
    return {"filename": file.filename, "content_type": file.content_type, "size": len(content_bytes)}