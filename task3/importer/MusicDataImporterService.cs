using System;
using System.Threading.Tasks;
using Grpc.Core;
using Npgsql;
using Datatransfer;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace Consumer.Services
{
    internal class MusicDataImporterService : DataImporter.DataImporterBase
    {
        private readonly NpgsqlConnection _connection;
        private readonly ILogger<MusicDataImporterService> _logger;
        private readonly IConfiguration _configuration;

        public MusicDataImporterService(NpgsqlConnection connection, ILogger<MusicDataImporterService> logger, IConfiguration configuration)
        {
            _connection = connection;
            _logger = logger;
            _configuration = configuration;
        }

        public override Task<ImportResponse> ImportMusicData(MusicDataRequest request, ServerCallContext context)
        {
            _logger.LogInformation($"Received data: {request.GroupName} - {request.MusicianName} - {request.InstrumentName} - {request.LabelName}");

            try
            {
                InsertNormalizedData(
                    request.GroupName,
                    request.MusicianName,
                    request.InstrumentName,
                    request.LabelName
                );

                return Task.FromResult(new ImportResponse
                {
                    Success = true,
                    Message = $"Successfully imported data for {request.MusicianName} from {request.GroupName}"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error importing data: {ex.Message}");
                return Task.FromResult(new ImportResponse
                {
                    Success = false,
                    Message = $"Failed to import data: {ex.Message}"
                });
            }
        }

        private void InsertNormalizedData(string groupName, string musicianName, string instrumentName, string labelName)
        {
            var pgConfig = _configuration.GetSection("Database:Postgres");

            using (var conn = new NpgsqlConnection(
                $"Host={pgConfig["Host"]};Port={pgConfig["Port"]};Username={pgConfig["User"]};Password={pgConfig["Password"]};Database=postgres"))
            {
                conn.Open();

                using (var cmd = new NpgsqlCommand($"SELECT 1 FROM pg_database WHERE datname = '{pgConfig["Database"]}'", conn))
                {
                    if (cmd.ExecuteScalar() == null)
                    {
                        using (var createDbCmd = new NpgsqlCommand($"CREATE DATABASE \"{pgConfig["Database"]}\"", conn))
                        {
                            createDbCmd.ExecuteNonQuery();
                            _logger.LogInformation($"Created database {pgConfig["Database"]}");
                        }
                    }
                }
            }

            using (var conn = new NpgsqlConnection(
                $"Host={pgConfig["Host"]};Port={pgConfig["Port"]};Username={pgConfig["User"]};Password={pgConfig["Password"]};Database={pgConfig["Database"]}"))
            {
                conn.Open();

                using (var cmd = new NpgsqlCommand(@"
                    CREATE TABLE IF NOT EXISTS labels (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE
                    );
                    CREATE TABLE IF NOT EXISTS groups (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE,
                        label_id INTEGER REFERENCES labels(id)
                    );
                    CREATE TABLE IF NOT EXISTS musicians (
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        group_id INTEGER REFERENCES groups(id)
                    );
                    CREATE TABLE IF NOT EXISTS instruments (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE
                    );
                    CREATE TABLE IF NOT EXISTS musician_instruments (
                        musician_id INTEGER REFERENCES musicians(id),
                        instrument_id INTEGER REFERENCES instruments(id),
                        PRIMARY KEY (musician_id, instrument_id)
                    );", conn))
                {
                    cmd.ExecuteNonQuery();
                }

                int labelId;
                using (var cmd = new NpgsqlCommand("SELECT id FROM labels WHERE name = @name", conn))
                {
                    cmd.Parameters.AddWithValue("name", labelName);
                    var result = cmd.ExecuteScalar();
                    if (result != null)
                    {
                        labelId = Convert.ToInt32(result);
                    }
                    else
                    {
                        using (var insertCmd = new NpgsqlCommand("INSERT INTO labels (name) VALUES (@name) RETURNING id", conn))
                        {
                            insertCmd.Parameters.AddWithValue("name", labelName);
                            labelId = Convert.ToInt32(insertCmd.ExecuteScalar());
                        }
                    }
                }

                int groupId;
                using (var cmd = new NpgsqlCommand("SELECT id FROM groups WHERE name = @name AND label_id = @labelId", conn))
                {
                    cmd.Parameters.AddWithValue("name", groupName);
                    cmd.Parameters.AddWithValue("labelId", labelId);
                    var result = cmd.ExecuteScalar();
                    if (result != null)
                    {
                        groupId = Convert.ToInt32(result);
                    }
                    else
                    {
                        using (var insertCmd = new NpgsqlCommand("INSERT INTO groups (name, label_id) VALUES (@name, @labelId) RETURNING id", conn))
                        {
                            insertCmd.Parameters.AddWithValue("name", groupName);
                            insertCmd.Parameters.AddWithValue("labelId", labelId);
                            groupId = Convert.ToInt32(insertCmd.ExecuteScalar());
                        }
                    }
                }

                int musicianId;
                using (var cmd = new NpgsqlCommand("SELECT id FROM musicians WHERE name = @name AND group_id = @groupId", conn))
                {
                    cmd.Parameters.AddWithValue("name", musicianName);
                    cmd.Parameters.AddWithValue("groupId", groupId);
                    var result = cmd.ExecuteScalar();
                    if (result != null)
                    {
                        musicianId = Convert.ToInt32(result);
                    }
                    else
                    {
                        using (var insertCmd = new NpgsqlCommand("INSERT INTO musicians (name, group_id) VALUES (@name, @groupId) RETURNING id", conn))
                        {
                            insertCmd.Parameters.AddWithValue("name", musicianName);
                            insertCmd.Parameters.AddWithValue("groupId", groupId);
                            musicianId = Convert.ToInt32(insertCmd.ExecuteScalar());
                        }
                    }
                }

                int instrumentId;
                using (var cmd = new NpgsqlCommand("SELECT id FROM instruments WHERE name = @name", conn))
                {
                    cmd.Parameters.AddWithValue("name", instrumentName);
                    var result = cmd.ExecuteScalar();
                    if (result != null)
                    {
                        instrumentId = Convert.ToInt32(result);
                    }
                    else
                    {
                        using (var insertCmd = new NpgsqlCommand("INSERT INTO instruments (name) VALUES (@name) RETURNING id", conn))
                        {
                            insertCmd.Parameters.AddWithValue("name", instrumentName);
                            instrumentId = Convert.ToInt32(insertCmd.ExecuteScalar());
                        }
                    }
                }

                using (var cmd = new NpgsqlCommand("SELECT 1 FROM musician_instruments WHERE musician_id = @musicianId AND instrument_id = @instrumentId", conn))
                {
                    cmd.Parameters.AddWithValue("musicianId", musicianId);
                    cmd.Parameters.AddWithValue("instrumentId", instrumentId);
                    if (cmd.ExecuteScalar() == null)
                    {
                        using (var insertCmd = new NpgsqlCommand("INSERT INTO musician_instruments (musician_id, instrument_id) VALUES (@musicianId, @instrumentId)", conn))
                        {
                            insertCmd.Parameters.AddWithValue("musicianId", musicianId);
                            insertCmd.Parameters.AddWithValue("instrumentId", instrumentId);
                            insertCmd.ExecuteNonQuery();
                        }
                    }
                }
            }

            _logger.LogInformation($"Successfully normalized and inserted data for {musicianName}");
        }
    }
}
