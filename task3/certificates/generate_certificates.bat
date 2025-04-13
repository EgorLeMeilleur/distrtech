#!/bin/bash

openssl req -x509 -newkey rsa:4096 -days 365 -nodes -keyout ca.key -out ca.pem -subj "/CN=Certificate-Authority"
openssl req -newkey rsa:4096 -nodes -keyout server.key -out server.csr -subj "/CN=192.168.100.3"
openssl req -newkey rsa:4096 -nodes -keyout client.key -out client.csr -subj "/CN=192.168.100.3"

openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.pem -days 365
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out client.pem -days 365

rm server.csr client.csr

echo "SSL certificates generated successfully"