using System.Net;
using System.Security.Cryptography.X509Certificates;
using Importer.Services;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);
var grpcConfig = builder.Configuration.GetSection("Server");
var grpcHost = grpcConfig["Host"] ?? "0.0.0.0";
var grpcPort = int.Parse(grpcConfig["Port"] ?? "5002");

builder.WebHost.ConfigureKestrel(options =>
{
    options.Listen(IPAddress.Parse(grpcHost), grpcPort, listenOptions =>
    {
        listenOptions.Protocols = HttpProtocols.Http2;
        listenOptions.UseHttps(httpsOptions =>
        {
            httpsOptions.ServerCertificate = new X509Certificate2("server.pfx", "password");
            httpsOptions.SslProtocols = System.Security.Authentication.SslProtocols.Tls12 |
                                          System.Security.Authentication.SslProtocols.Tls13;
        });
    });
});

builder.Services.AddGrpc(); 

var pgConfig = builder.Configuration.GetSection("Postgres");
var connectionString = $"Host={pgConfig["Host"]};Port={pgConfig["Port"]};Username={pgConfig["User"]};Password={pgConfig["Password"]};Database={pgConfig["Database"]}";
builder.Services.AddTransient(_ => new NpgsqlConnection(connectionString));

builder.Services.AddSingleton(builder.Configuration);

var app = builder.Build();

app.MapGrpcService<MusicDataImporterService>();

app.MapGet("/", () => $"Music Data Importer Service is running on {grpcHost}:{grpcPort}");

app.Run();
