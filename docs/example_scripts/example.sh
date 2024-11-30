#!/usr/bin/env sh


#!/usr/bin/env sh

# Leer los parámetros JSON pasados al script
request=$1

# Parsear los parámetros JSON usando `jq` (asegúrate de tener `jq` instalado)
method=$(echo "$request" | jq -r '.method')
client=$(echo "$request" | jq -r '.client')
datetime=$(echo "$request" | jq -r '.datetime')

echo "Method: $method"
echo "Client: $client"
echo "Datetime: $datetime"
