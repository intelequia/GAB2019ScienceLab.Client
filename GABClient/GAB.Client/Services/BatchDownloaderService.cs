using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.ApplicationInsights;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace GAB.Client.Services
{
    public class BatchDownloaderService : IHostedService, IDisposable
    {
        private readonly IConfiguration _configuration;
        private readonly ILogger _logger;
        private Timer _timer;
        private readonly TelemetryClient _telemetry = new TelemetryClient();

        public static bool Started { get; set; }
        public static ServiceStatusEnum Status { get; set; }


        public BatchDownloaderService(IConfiguration configuration, ILogger<BatchDownloaderService> logger)
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
                _logger.LogInformation("Batch downloader background service is starting.");
                Directory.CreateDirectory("/app/inputs");
                Directory.CreateDirectory("/app/outputs");
                _timer = new Timer(DoWork, null, TimeSpan.Zero,
                    TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:DownloaderIntervalInSeconds")));

                Started = true;
                return Task.CompletedTask;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error starting downloader service");
                _telemetry.TrackException(ex);
                throw;
            }
        }

        private void DoWork(object state)
        {
            try
            {
                // Is the upload queue
                if (Directory.GetFiles("/app/outputs", "*.result", SearchOption.AllDirectories).Length >
                    _configuration.GetValue<int>("BatchClient:MaxPendingUploads"))
                {
                    _logger.LogWarning("Maximum pending uploads reached. Pausing downloader service.");
                    Status = ServiceStatusEnum.Paused;
                    return;
                }

                _timer?.Change(Timeout.Infinite, 0);
                Status = ServiceStatusEnum.Running;

                var pendingFilesCount = Directory.GetFiles("/app/inputs", "*.").Length;
                if (pendingFilesCount <= 1)
                {
                    _telemetry.TrackTrace("Downloading new batch...");
                    _logger.LogInformation("Downloading new batch...");
                    var batchClient = new BatchClient(_configuration);
                    var result = batchClient.GetNewBatchAsync().Result;
                    foreach (var output in result.Outputs)
                    {
                        output.BatchId = result.BatchId;
                        File.WriteAllText($"/app/inputs/{output.InputId}.json", JsonConvert.SerializeObject(output));
                    }
                    var wc = new WebClient();
                    foreach (var input in result.Inputs)
                    {
                        var fileName = "/app/inputs/" + input.InputId;
                        wc.DownloadFile(new Uri(input.Parameters), $"{fileName}.part");
                        File.Move($"{fileName}.part", fileName);
                    }

                    _telemetry.TrackTrace($"Downloaded batch {result.BatchId}");
                    _logger.LogInformation($"Downloaded batch {result.BatchId}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading new batch");
                _telemetry.TrackException(ex);
            }
            _timer?.Change(TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:DownloaderIntervalInSeconds")), 
                TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:DownloaderIntervalInSeconds")));
            Status = ServiceStatusEnum.Idle;
        }

        public Task StopAsync(CancellationToken cancellationToken)
        {
            try
            {
                Started = false;
                _logger.LogInformation("Batch downloader background service is stopping.");
                _timer?.Change(Timeout.Infinite, 0);
                // Return files to the repository
                var pendingFiles = System.IO.Directory.GetFiles("/app/inputs", "*.");
                if (pendingFiles.Length > 0)
                {
                    _telemetry.TrackTrace($"Returning {pendingFiles.Length} inputs to the repository...");
                    var batchClient = new BatchClient(_configuration);
                    batchClient.CancelInputsAsync(pendingFiles.Select(Path.GetFileName).ToArray()).ConfigureAwait(false);
                    foreach (var pendingFile in pendingFiles)
                    {
                        File.Delete(pendingFile);
                    }
                }
                // Delete json info
                foreach (var pendingFile in Directory.GetFiles("/app/inputs", "*.json"))
                {
                    File.Delete(pendingFile);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error stopping batch downloader service");
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
