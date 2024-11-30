# main.py

import json
import time
import subprocess
import logging

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyngrok import ngrok
from starlette.staticfiles import StaticFiles


# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Iniciar el túnel ngrok en el puerto 8001
public_url = ngrok.connect(8081).public_url
print(f" * Túnel ngrok establecido en {public_url}")

# Iniciar la aplicación FastAPI
app = FastAPI()

app.mount("/static", StaticFiles(directory="./public/static"), name="static")

# Directorio de plantillas
templates = Jinja2Templates(directory="templates")

# Lista para almacenar las peticiones recibidas
peticiones_recibidas = []

# Lista de websockets conectados
websockets_conectados = []


@app.post("/webhook")
async def webhook(request: Request):
    info_peticion = await get_request_info(request)

    peticiones_recibidas.insert(0, info_peticion)
    data = json.dumps({'event': 'new_request', 'data': info_peticion})
    for websocket in websockets_conectados:
        await websocket.send_text(data)

    return {"message": "Webhook recibido"}

@app.post("/scripts/{script_name}")
async def run_script(script_name: str, request: Request):
    script_path = f"scripts/{script_name}"
    logger.info(f"Running script: {script_path}")

    info_peticion = await get_request_info(request)

    try:
        # Ejecutar el script y capturar la salida
        result = subprocess.run([script_path, json.dumps(info_peticion)], capture_output=True, text=True,
                                check=True)
        output = result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running the script {script_path}: {e.stderr}")
        return {"error": f"Error running the script {script_path}: {e.stderr}"}, 500
    except FileNotFoundError:
        return {"error": "Not found"}, 404

    info_peticion['script_output'] = output
    peticiones_recibidas.insert(0, info_peticion)
    data = json.dumps({'event': 'new_request', 'data': info_peticion})
    for websocket in websockets_conectados:
        await websocket.send_text(data)

    return {"output": output}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "public_url": public_url})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websockets_conectados.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantener la conexión abierta
    except WebSocketDisconnect:
        websockets_conectados.remove(websocket)

@app.get("/api/peticiones")
async def get_peticiones():
    return peticiones_recibidas


async def get_request_info(request: Request):
    headers = dict(request.headers)
    body = await request.body()
    body_str = body.decode('utf-8')
    try:
        json_body = await request.json()
    except:
        json_body = None

    return {
        'headers': headers,
        'method': request.method,
        'body': body_str,
        'json': json_body,
        'client': request.client.host,
        'datetime': time.strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    # TODO: Puerto configurable
    # TODO: Activar o no la recarga automática con reload

    uvicorn.run(app, host="0.0.0.0", port=8081)
