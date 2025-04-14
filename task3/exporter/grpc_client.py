import grpc
import data_transfer_pb2
import data_transfer_pb2_grpc

class GRPCDataImporterClient:
    def __init__(self, host, port, ca_cert_path):
        with open(ca_cert_path, 'rb') as f:
            trusted_certs = f.read()
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
        self.channel = grpc.secure_channel(f"{host}:{port}", credentials)
        self.stub = data_transfer_pb2_grpc.DataImporterStub(self.channel)

    def import_music_data(self, transactions):
        def request_iterator():
            for transaction_data in transactions:
                yield data_transfer_pb2.MusicDataRequest(
                    group_name=transaction_data['group_name'],
                    musician_name=transaction_data['musician_name'],
                    instrument_name=transaction_data['instrument_name'],
                    label_name=transaction_data['label_name']
                )
        
        response = self.stub.ImportMusicData(request_iterator())
        return response.success, response.message


    def close(self):
        if self.channel:
            self.channel.close()
