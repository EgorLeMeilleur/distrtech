python -m grpc_tools.protoc -I=proto --python_out=servers/t_analyzer --grpc_python_out=servers/t_analyzer proto/sensor_analyzer.proto
protoc -I=proto --grpc_out=clients/client_t --plugin=protoc-gen-grpc=$(which grpc_cpp_plugin) proto/sensor_analyzer.proto
protoc -I=proto --cpp_out=clients/client_t proto/sensor_analyzer.proto

docker network create farm_net
docker volume create fifo_volume

docker build -t client_t ./clients/client_t
docker run -e CONSUL_HOST=172.30.203.56 -e RABBITMQ_HOST=172.30.203.56 client_t

docker build -t client_h ./clients/client_h
docker run -e CONSUL_HOST=172.30.203.56 -e RABBITMQ_HOST=172.30.203.56 client_h

docker build -t client_video ./clients/client_video
docker run -e CONSUL_HOST=172.30.203.56 -e RABBITMQ_HOST=172.30.203.56 client_video

docker build -t server ./servers/t_analyzer
docker run -e CONSUL_HOST=172.30.203.56 -e RABBITMQ_HOST=172.30.203.56 -v fifo_volume:/shared server_t

docker build -t server_h ./servers/h_analyzer
docker run -e CONSUL_HOST=172.30.203.56 -e RABBITMQ_HOST=172.30.203.56 -v fifo_volume:/shared server_h

docker build -t server_video ./servers/video_analyzer
docker run -e CONSUL_HOST=172.30.203.56 -e RABBITMQ_HOST=172.30.203.56 -v fifo_volume:/shared server_video

docker build -t aggregator ./servers/aggregator
docker run -e DB_HOST=172.30.203.56 -v fifo_volume:/shared aggregator

docker-compose -f infrastructure/docker-compose.services.yml up --build
docker-compose -f infrastructure/docker-compose.clients.yml up --build
docker-compose -f infrastructure/docker-compose.servers.yml up --build

