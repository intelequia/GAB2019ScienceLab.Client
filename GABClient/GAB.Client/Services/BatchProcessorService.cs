using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.ApplicationInsights;
using Microsoft.DotNet.PlatformAbstractions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace GAB.Client.Services
{
    public class BatchProcessorService : IHostedService, IDisposable
    {
        private readonly IConfiguration _configuration;
        private readonly ILogger _logger;
        private Timer _timer;
        private readonly TelemetryClient _telemetry = new TelemetryClient();
        public static bool Started { get; set; }
        public static ServiceStatusEnum Status { get; set; }
        public static string InputId { get; set; }


        public BatchProcessorService(IConfiguration configuration, ILogger<BatchProcessorService> logger)
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
                _logger.LogInformation("Batch processor background service is starting.");
                Directory.CreateDirectory("/app/inputs");
                Directory.CreateDirectory("/app/processing");
                Directory.CreateDirectory("/app/errors");
                Directory.CreateDirectory("/app/outputs");
                _timer = new Timer(DoWork, null, TimeSpan.Zero,
                    TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:ProcessorIntervalInSeconds")));
                Started = true;

                return Task.CompletedTask;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error starting processor service");
                _telemetry.TrackException(ex);
                throw;
            }
        }

        private void DoWork(object state)
        {
            InputId = string.Empty;
            var processingfile = string.Empty;
            try
            {
                Status = ServiceStatusEnum.Running;
                _timer?.Change(Timeout.Infinite, 0);

                var pendingFiles = Directory.GetFiles("/app/inputs", "*.");
                if (pendingFiles.Length > 0)
                {
                    // Move the input to processing
                    var file = pendingFiles.First();
                    InputId = Path.GetFileName(file);
                    processingfile = $"/app/processing/{InputId}";
                    File.Move(file, processingfile);
                    File.Move(file + ".json", processingfile + ".json");
                    _logger.LogInformation($"Processing input {InputId}...");
                    _telemetry.TrackTrace($"Processing input {InputId}...");


                    // Call pipeline 1
                    _logger.LogInformation($"Executing pipeline 1 on input {InputId}...");
                    var result1 = "";
                    var start1 = new ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = $"/app/wwwroot/ml/pipeline1.py -i {processingfile}",
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                    };
                    using (var process = Process.Start(start1))
                    {
                        var stderr = "";
                        var timedOut = !process.WaitForExit(_configuration.GetValue<int>("BatchClient:BatchProcessingTimeoutInSeconds") * 1000); // Waits for 20min maximum
                        using (var reader = process.StandardOutput)
                        {
                            stderr = process.StandardError
                                .ReadToEnd(); // Here are the exceptions from our Python script
                            result1 = reader
                                .ReadToEnd(); // Here is the result of StdOut(for example: print "test")                            
                        }
                        _logger.LogInformation(result1);
                        if (timedOut)
                        {
                            throw new ApplicationException($"Error processing input (Timeout): {stderr}");
                        }
                        if (process.ExitCode != 0)
                        {
                            throw new ApplicationException($"Error processing input: {stderr}");
                        }
                    }

                    // Process the input
                    _logger.LogInformation($"Executing pipeline 2 on input {InputId}...");
                    var result2 = "";
                    var start2 = new ProcessStartInfo
                    {
                        FileName = "python3",
                        Arguments = $"/app/wwwroot/ml/pipeline2.py /app/wwwroot/ml/pipeline2/learn-GAB-Tess-noblackman1024-stsflat-2casts-1800-full.pkl {processingfile}_data.npz {processingfile}",
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,                        
                    };
                    using (var process = Process.Start(start2))
                    {
                        var stderr = "";
                        var timedOut = !process.WaitForExit(_configuration.GetValue<int>("BatchClient:BatchProcessingTimeoutInSeconds") * 1000); // Waits for 20min maximum
                        using (var reader = process.StandardOutput)
                        {
                            stderr = process.StandardError
                                .ReadToEnd(); // Here are the exceptions from our Python script
                            result2 = reader
                                .ReadToEnd(); // Here is the result of StdOut(for example: print "test")                            
                        }
                        _logger.LogInformation(result2);
                        if (timedOut)
                        {
                            throw new ApplicationException($"Error processing input (Timeout): {stderr}");
                        }
                        if (process.ExitCode != 0)
                        {
                            throw new ApplicationException($"Error processing input: {stderr}");
                        }
                    }
                    
                    _logger.LogInformation($"Input {InputId} processed:");
                    _telemetry.TrackEvent("InputProcessed", new Dictionary<string, string>()
                    {
                        {"InputId", InputId},
                        {"ContainerId", Environment.MachineName },
                        {"ClientVersion", Assembly.GetExecutingAssembly().GetCustomAttribute<AssemblyFileVersionAttribute>().Version },
                        {"Result", result2}
                    });

                    // Move results to outputs folder
                    Directory.CreateDirectory($"/app/outputs/{InputId}");
                    File.Move(processingfile + ".json", $"/app/outputs/{InputId}/{InputId}.json");
                    var outputs = Directory.GetFiles($"/app/processing", $"{InputId}_*.*");
                    foreach (var output in outputs)
                    {
                        File.Move(output, $"/app/outputs/{InputId}/{Path.GetFileName(output)}");
                    }                    
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing input");
                _telemetry.TrackException(ex);
                if (!string.IsNullOrEmpty(processingfile) && File.Exists(processingfile))
                {
                    File.Move(processingfile, $"/app/errors/{InputId}");
                }
                if (!string.IsNullOrEmpty(processingfile) && File.Exists(processingfile + ".json"))
                {
                    File.Move(processingfile + ".json", $"/app/errors/{InputId}.json");
                }

                //TODO Notifiy Batch Server with processing error?
            }
            finally
            {
                if (!string.IsNullOrEmpty(processingfile) && File.Exists(processingfile))
                {
                    File.Delete(processingfile);
                }
            }
            Status = ServiceStatusEnum.Idle;
            InputId = "";
            _timer?.Change(TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:ProcessorIntervalInSeconds")),
                TimeSpan.FromSeconds(_configuration.GetValue<int>("BatchClient:ProcessorIntervalInSeconds")));
        }

        public Task StopAsync(CancellationToken cancellationToken)
        {
            try
            {
                Started = false;
                _logger.LogInformation("Batch processor background service is stopping.");
                _timer?.Change(Timeout.Infinite, 0);

                // Return files to the repository
                var pendingFiles = Directory.GetFiles("/app/processing", "*.");
                if (pendingFiles.Length > 0)
                {
                    _logger.LogInformation($"Returning {pendingFiles.Length} inputs to the repository...");
                    _telemetry.TrackTrace($"Returning {pendingFiles.Length} inputs to the repository...");
                    var batchClient = new BatchClient(_configuration);
                    batchClient.CancelInputsAsync(pendingFiles.Select(Path.GetFileName).ToArray()).ConfigureAwait(false);
                    foreach (var pendingFile in pendingFiles)
                    {
                        File.Delete(pendingFile);
                    }
                }
                // Delete json info
                foreach (var pendingFile in Directory.GetFiles("/app/processing", "*.json"))
                {
                    File.Delete(pendingFile);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error stopping processor service");
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
