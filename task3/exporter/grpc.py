import grpc
import logging
import data_transfer_pb2
import data_transfer_pb2_grpc

class GRPCDataImporterClient:
    def __init__(self, host, port, ca_cert_path):
        with open(ca_cert_path, 'rb') as f:
            trusted_certs = f.read()
        credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
        self.channel = grpc.secure_channel(f"{host}:{port}", credentials)
        self.stub = data_transfer_pb2_grpc.DataImporterStub(self.channel)

    def import_music_data(self, group_name, musician_name, instrument_name, label_name):
        request = data_transfer_pb2.MusicDataRequest(
            group_name=group_name,
            musician_name=musician_name,
            instrument_name=instrument_name,
            label_name=label_name
        )
        try:
            response = self.stub.ImportMusicData(request)
            return True, response.message
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return False, str(e)

    def close(self):
        if self.channel:
            self.channel.close()
