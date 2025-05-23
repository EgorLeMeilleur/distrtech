SERVERS_DIR := servers
CLIENTS_DIR := clients

TEMP_SERVER := $(SERVERS_DIR)/server_t.py
HUMID_SERVER := $(SERVERS_DIR)/server_h.py
VIDEO_SERVER := $(SERVERS_DIR)/server_video.py
AGGREGATOR := $(SERVERS_DIR)/aggregator.py

TEMP_CLIENT := $(CLIENTS_DIR)/client_t.py
HUMID_CLIENT := $(CLIENTS_DIR)/client_h.py
VIDEO_CLIENT := $(CLIENTS_DIR)/client_video.py

.PHONY: server_t server_h server_video aggregator client_t client_h client_video

server_t:
	@echo "Starting Temperature Server..."
	$(PYTHON) $(TEMP_SERVER)

server_h:
	@echo "Starting Humidity Server..."
	$(PYTHON) $(HUMID_SERVER)

server_video:
	@echo "Starting Video Server..."
	$(PYTHON) $(VIDEO_SERVER)

aggregator:
	@echo "Starting Aggregator..."
	$(PYTHON) $(AGGREGATOR)

client_t:
	@echo "Starting Temperature Client..."
	$(PYTHON) $(TEMP_CLIENT)

client_h:
	@echo "Starting Humidity Client..."
	$(PYTHON) $(HUMID_CLIENT)

client_video:
	@echo "Starting Video Client..."
	$(PYTHON) $(VIDEO_CLIENT)
