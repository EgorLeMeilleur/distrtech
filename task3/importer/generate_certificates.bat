@echo off

openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=My Local CA"

openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=192.168.100.10" -addext "subjectAltName=IP:192.168.100.10"

echo subjectAltName=IP:192.168.100.10 > extensions.cnf

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -extfile extensions.cnf

openssl pkcs12 -export -out server.pfx -inkey server.key -in server.crt -certfile ca.crt -password pass:password

del extensions.cnf
del server.csr
del ca.srl

echo Certificates generated successfully!