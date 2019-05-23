using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using GAB.Client.Models;
using Microsoft.ApplicationInsights;
using Microsoft.DotNet.PlatformAbstractions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.WindowsAzure.Storage.Blob;
using Newtonsoft.Json;

namespace GAB.Client.Services
{
    public class BatchUploaderService : IHostedService, IDisposable
    {
        private readonly IConfiguration _configuration;
        private readonly ILogger _logger;
        private Timer _timer;
        private readonly TelemetryClient _telemetry = new TelemetryClient();
        public static bool Started { get; set; }
        public static ServiceStatusEnum Status { get; set; }


        public BatchUploaderService(IConfiguration configuration, ILogger<BatchUploaderService> logger)
        {
            _configuration = configuration;
            _logger = logger;
            Started = false;
            Status = ServiceStatusEnum.Idle;
        }

        public Task StartAsync(CancellationToken cancellationToken)
        {
            try
            {
                _logger.LogInformation("Batch uploader background service is starting.");
                Directory.CreateDirectory("/app/outputs");
                _timer = new Timer(DoWork, null, TimeSpan.Zero,
                    TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:UploaderIntervalInSeconds")));

                Started = true;
                return Task.CompletedTask;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error starting uploader service");
                _telemetry.TrackException(ex);
                throw;
            }
        }

        //TODO make this async
        private void DoWork(object state)
        {
            try
            {
                _timer?.Change(Timeout.Infinite, 0);
                Status = ServiceStatusEnum.Running;

                var pendingFiles = Directory.GetFiles("/app/outputs", "*.result", SearchOption.AllDirectories);
                if (pendingFiles.Length > 0)
                {
                    var batchClient = new BatchClient(_configuration);                    
                    foreach (var pendingFile in pendingFiles)
                    {
                        // Package
                        var folder = Path.GetDirectoryName(pendingFile);
                        var inputId = int.Parse(Path.GetFileName(folder));

                        try
                        {
                            Retry.Do(() =>
                            {
                                var logMsg = "";
                                var inputInfo =
                                    JsonConvert.DeserializeObject<OutputResult>(
                                        File.ReadAllText($"{folder}/{inputId}.json"));
                                var blob = new CloudBlockBlob(new Uri(inputInfo.LightCurvesUploadUri));
                                logMsg = $"Uploading light curve for input {inputId} of batch {inputInfo.BatchId}...";
                                _logger.LogInformation(logMsg);
                                _telemetry.TrackTrace(logMsg);
                                var ok = UploadBlob(blob, $"{folder}/{inputId}_data.npz").Result;

                                // Upload
                                logMsg = $"Uploading output for input {inputId} of batch {inputInfo.BatchId}...";
                                _logger.LogInformation(logMsg);
                                _telemetry.TrackTrace(logMsg);
                                var outputContent =
                                    JsonConvert.DeserializeObject<OutputContent>(File.ReadAllText(pendingFile));
                                outputContent.lc =
                                    inputInfo.LightCurvesUploadUri.Substring(0,
                                        inputInfo.LightCurvesUploadUri.IndexOf('?'));
                                outputContent.inputid = inputId;
                                outputContent.containerid = Environment.MachineName;
                                outputContent.clientversion = Assembly.GetExecutingAssembly()
                                    .GetCustomAttribute<AssemblyFileVersionAttribute>().Version;
                                var result = batchClient.UploadOutputAsync(inputId, outputContent).Result;
                                logMsg =
                                    $"Output for input {inputId} of batch {inputInfo} uploaded successfully (output {result.OutputId})";
                                _logger.LogInformation(logMsg);
                                _telemetry.TrackTrace(logMsg);
                            }, TimeSpan.FromSeconds(5));
                        }
                        finally
                        {
                            if (Directory.Exists(folder))
                            {
                                // Clean
                                Directory.Delete(folder, true);
                            }
                        }
                    }
                }
                
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error uploading output");
                _telemetry.TrackException(ex);
            }            
            _timer?.Change(TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:UploaderIntervalInSeconds")),
                TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:UploaderIntervalInSeconds")));
            Status = ServiceStatusEnum.Idle;
        }

        private async Task<bool> UploadBlob(CloudBlockBlob blob, string filename)
        {
            await blob.UploadFromFileAsync(filename);
            return true;
        }


        public Task StopAsync(CancellationToken cancellationToken)
        {
            try
            {
                Started = false;
                _logger.LogInformation("Batch uploader background service is stopping.");
                _timer?.Change(Timeout.Infinite, 0);

            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error stopping uploader service");
                _telemetry.TrackException(ex);
            }
            return Task.CompletedTask;
        }

        public void Dispose()
        {
            _timer?.Dispose();
        }
    }
}
