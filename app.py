# main.py
import argparse
import json
import time
import os
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict, deque

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyngrok import ngrok
from starlette.staticfiles import StaticFiles

app = FastAPI()

# Get resource paths from environment variables or use defaults
templates_dir = os.environ.get("TEMPLATES_DIR", "templates")
public_dir = os.environ.get("PUBLIC_DIR", "./public")

app.mount("/static", StaticFiles(directory=os.path.join(public_dir, "static")), name="static")

# Directorio de plantillas
templates = Jinja2Templates(directory=templates_dir)

# Lista para almacenar las peticiones recibidas
peticiones_recibidas = []

# Lista de websockets conectados
websockets_conectados = []

# Sistema de métricas similar a webhook_server.py
stats = {
    "total_requests": 0,
    "requests_by_method": defaultdict(int),
    "requests_by_endpoint": defaultdict(int),
    "requests_by_client": defaultdict(int),
    "requests_by_status": defaultdict(int),
    "start_time": time.time(),
    "recent_requests": deque(maxlen=100),  # Últimas 100 peticiones
    "error_count": 0
}


def parser_args():
    parser = argparse.ArgumentParser(description='Webhook receiver API')
    parser.add_argument('--port', type=int, default=8081, help='Port to run the API')
    args = parser.parse_args()
    return args

args = parser_args()
# Iniciar el túnel ngrok en el puerto elegido
public_url = ngrok.connect(args.port).public_url
print(f" * Túnel ngrok establecido en {public_url}")


@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Obtener los detalles de la petición
        headers = dict(request.headers)
        body = await request.body()
        body_str = body.decode('utf-8')
        try:
            json_body = await request.json()
        except:
            json_body = None

        # Extraer información para métricas
        method = request.method
        endpoint = str(request.url.path)
        client_ip = request.client.host
        received_at = datetime.now().isoformat()

        info_peticion = {
            'headers': headers,
            'method': method,
            'body': body_str,
            'json': json_body,
            'client': client_ip,
            'datetime': time.strftime("%Y-%m-%d %H:%M:%S"),
            'received_at': received_at
        }

        # Actualizar estadísticas
        stats["total_requests"] += 1
        stats["requests_by_method"][method] += 1
        stats["requests_by_endpoint"][endpoint] += 1
        stats["requests_by_client"][client_ip] += 1
        stats["requests_by_status"]["success"] += 1

        # Guardar petición reciente para métricas
        request_info = {
            "received_at": received_at,
            "method": method,
            "endpoint": endpoint,
            "client_ip": client_ip,
            "payload_size": len(body_str),
            "headers": {k: v for k, v in headers.items() if k.lower().startswith('x-')},
            "status": "success"
        }
        stats["recent_requests"].append(request_info)

        peticiones_recibidas.insert(0, info_peticion)

        # Notificar a los websockets conectados
        data = json.dumps({'event': 'new_request', 'data': info_peticion})
        for websocket in websockets_conectados:
            await websocket.send_text(data)

        return {"message": "Webhook recibido"}

    except Exception as e:
        stats["error_count"] += 1
        stats["requests_by_status"]["error"] += 1
        return {"message": f"Error procesando webhook: {str(e)}"}, 500


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


@app.get("/v1/api")
async def get_metrics():
    """Endpoint para obtener métricas del servidor webhook similar a webhook_server.py."""
    uptime = time.time() - stats["start_time"]
    
    return {
        "uptime_seconds": round(uptime, 2),
        "uptime_formatted": f"{int(uptime // 3600):02d}:{int((uptime % 3600) // 60):02d}:{int(uptime % 60):02d}",
        "total_requests": stats["total_requests"],
        "requests_per_second": round(stats["total_requests"] / uptime, 2) if uptime > 0 else 0,
        "error_count": stats["error_count"],
        "error_rate": round(stats["error_count"] / max(stats["total_requests"], 1) * 100, 2),
        "requests_by_method": dict(stats["requests_by_method"]),
        "requests_by_endpoint": dict(stats["requests_by_endpoint"]),
        "requests_by_client": dict(stats["requests_by_client"]),
        "requests_by_status": dict(stats["requests_by_status"]),
        "recent_requests_count": len(stats["recent_requests"])
    }


@app.get("/v1/api/recent")
async def get_recent_requests():
    """Endpoint para obtener las peticiones recientes."""
    limit = 10  # Por defecto 10, se puede hacer configurable
    recent = list(stats["recent_requests"])[-limit:]
    
    return {
        "recent_requests": recent,
        "count": len(recent),
        "total_available": len(stats["recent_requests"])
    }


@app.get("/v1/api/health")
async def health_check():
    """Health check del servidor webhook."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_requests": stats["total_requests"],
        "uptime_seconds": round(time.time() - stats["start_time"], 2)
    }


@app.post("/v1/api/reset")
async def reset_stats():
    """Reset de las estadísticas (útil para nuevos tests)."""
    global stats
    stats = {
        "total_requests": 0,
        "requests_by_method": defaultdict(int),
        "requests_by_endpoint": defaultdict(int),
        "requests_by_client": defaultdict(int),
        "requests_by_status": defaultdict(int),
        "start_time": time.time(),
        "recent_requests": deque(maxlen=100),
        "error_count": 0
    }
    
    return {
        "status": "reset",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/v1/api/webhook-url")
async def get_webhook_url():
    """Endpoint para obtener la URL del webhook generado por ngrok."""
    return {
        "webhook_url": f"{public_url}/webhook",
        "public_url": public_url,
        "ngrok_url": public_url,
        "endpoints": {
            "webhook": f"{public_url}/webhook",
            "dashboard": public_url,
            "metrics": f"{public_url}/v1/api",
            "health": f"{public_url}/v1/api/health"
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    args = parser_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
