docker network create distrnet

docker-compose -f docker-compose.services.yml up --build
docker-compose -f docker-compose.clients.yml up --build
docker-compose -f docker-compose.servers.yml up --build

python servers/server_video.py
python servers/server_t.py
python servers/server_h.py
python servers/aggregator.py
python clients/client_video.py
python clients/client_t.py
python clients/client_h.py

