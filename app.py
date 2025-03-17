# main.py

import json
import time

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyngrok import ngrok
from starlette.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="./public/static"), name="static")

# Directorio de plantillas
templates = Jinja2Templates(directory="templates")

# Lista para almacenar las peticiones recibidas
peticiones_recibidas = []

# Lista de websockets conectados
websockets_conectados = []

# Iniciar el túnel ngrok en el puerto 8000
public_url = ngrok.connect(8081).public_url
print(f" * Túnel ngrok establecido en {public_url}")


@app.post("/webhook")
async def webhook(request: Request):
    # Obtener los detalles de la petición
    headers = dict(request.headers)
    body = await request.body()
    body_str = body.decode('utf-8')
    try:
        json_body = await request.json()
    except:
        json_body = None

    info_peticion = {
        'headers': headers,
        'method': request.method,
        'body': body_str,
        'json': json_body,
        'client': request.client.host,
        'datetime': time.strftime("%Y-%m-%d %H:%M:%S")
    }

    peticiones_recibidas.insert(0, info_peticion)

    # Notificar a los websockets conectados
    data = json.dumps({'event': 'new_request', 'data': info_peticion})
    for websocket in websockets_conectados:
        await websocket.send_text(data)

    return {"message": "Webhook recibido"}


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


@app.delete("/api/peticiones")
async def delete_peticiones():
    global peticiones_recibidas
    peticiones_recibidas = []
    
    # Notificar a los websockets conectados que se han eliminado todas las peticiones
    data = json.dumps({'event': 'clear_requests'})
    for websocket in websockets_conectados:
        await websocket.send_text(data)
    
    return {"message": "Todas las peticiones han sido eliminadas"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
