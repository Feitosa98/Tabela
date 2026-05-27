import os
import subprocess
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app import processar_pdf

BASE_DIR = Path(__file__).parent
ENTRADA_DIR = BASE_DIR / "entrada"
SAIDA_DIR = BASE_DIR / "saida"

app = FastAPI()

# Servir arquivos estáticos (HTML, CSS, JS)
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_file = static_dir / "index.html"
    return index_file.read_text(encoding="utf-8")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Apenas arquivos PDF são permitidos."})
    
    file_path = ENTRADA_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    json_out = SAIDA_DIR / f"{file.filename.replace('.pdf', '')}_extraido.json"
    
    try:
        final_json_path = processar_pdf(pdf_path=file_path, json_out=json_out)
        with open(final_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"status": "success", "message": "Extração concluída com sucesso!", "data": data, "json_file": Path(final_json_path).name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/publicar")
async def publicar_git():
    try:
        subprocess.run(["git", "add", "saida/"], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "commit", "-m", "Atualização da tabela de emolumentos via Extrator Web"], cwd=str(BASE_DIR), check=True)
        
        subprocess.run(["git", "push"], cwd=str(BASE_DIR), check=True)
        
        return {"status": "success", "message": "Arquivos adicionados e enviados ao Git com sucesso!"}
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": f"Erro ao executar o Git: verifique se o repositório foi inicializado."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
