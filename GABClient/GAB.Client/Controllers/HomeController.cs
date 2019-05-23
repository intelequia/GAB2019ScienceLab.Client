using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using GAB.Client.Models;
using System.IO;
using System.Reflection;
using GAB.Client.Services;

namespace GAB.Client.Controllers
{
    public class HomeController : Controller
    {
        public IActionResult Index()
        {
            ViewData.Add("Downloads", Directory.GetFiles("/app/inputs", "*.").Length);
            ViewData.Add("Uploads", Directory.GetFiles("/app/outputs", "*.result", SearchOption.AllDirectories).Length);
            ViewData.Add("BatchDownloader.Started", BatchDownloaderService.Started);
            ViewData.Add("BatchDownloader.Status", BatchDownloaderService.Status);
            ViewData.Add("BatchProcessor.Started", BatchProcessorService.Started); 
            ViewData.Add("BatchProcessor.Status", BatchProcessorService.Status);
            ViewData.Add("BatchProcessor.InputId", BatchProcessorService.InputId);
            ViewData.Add("BatchUploader.Started", BatchUploaderService.Started);
            ViewData.Add("BatchUploader.Status", BatchUploaderService.Status);

            ViewData.Add("Version", "v" + Assembly.GetExecutingAssembly().GetCustomAttribute<AssemblyFileVersionAttribute>().Version);

            // Autorefresh every 10 seconds
            Response.Headers.Add("Refresh", "10");
            return View();
        }

        public IActionResult Logs()
        {
            var logBytes = System.IO.File.ReadAllBytes("/app/logs/" + DateTime.Today.ToString("yyyy.MM.dd") + ".log");
            return File(logBytes, "text/plain");
        }

        public IActionResult About()
        {
            ViewData.Add("Version", "v" + Assembly.GetExecutingAssembly().GetCustomAttribute<AssemblyFileVersionAttribute>().Version);
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
