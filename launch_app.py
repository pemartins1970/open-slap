import os
import sys
import uvicorn

# Adiciona a raiz do projeto ao sys.path
sys.path.append(os.getcwd())

if __name__ == "__main__":
    uvicorn.run("backend.main_auth:app", host="127.0.0.1", port=5150, reload=True)
