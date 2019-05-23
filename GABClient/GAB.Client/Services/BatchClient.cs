using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Reflection;
using System.Text.Encodings.Web;
using System.Threading.Tasks;
using GAB.Client.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Net.Http.Headers;
using Newtonsoft.Json;

namespace GAB.Client.Services
{
    public class BatchClient
    {
        private const int DefaultBatchSize = 10;

        private readonly IConfiguration _configuration;

        private string _baseUrl;
        public string BaseUrl
        {
            get
            {
                if (string.IsNullOrEmpty(_baseUrl))
                {
                    _baseUrl = _configuration.GetValue<string>("BatchServer:BaseUrl");
                    if (!_baseUrl.EndsWith('/'))
                        _baseUrl += "/";
                }
                return _baseUrl;
            }
        }

        private static ProductInfoHeaderValue UserAgent
        {
            get
            {
                var assemblyName = Assembly.GetEntryAssembly().GetName();
                return new ProductInfoHeaderValue(assemblyName.Name, assemblyName.Version.ToString());
            }
        }
           

        public BatchClient(IConfiguration configuration)
        {
            _configuration = configuration;
        }

        public async Task<GetNewBatchResult> GetNewBatchAsync()
        {
            var batchSize = _configuration.GetValue<int>("BatchServer:BatchSize");
            if (batchSize == 0)
            {
                batchSize = DefaultBatchSize;
            }

            using (var httpClient = new HttpClient())
            {
                httpClient.DefaultRequestHeaders.UserAgent.Add(UserAgent);
                var query = $"batchSize={batchSize}" +
                            $"&email={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:Email"))}" +
                            $"&fullName={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:FullName"))}" +
                            $"&teamName={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:TeamName"))}" +
                            $"&companyName={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:CompanyName"))}" +
                            $"&location={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:LabKeyCode"))}" +
                            $"&countryCode={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:CountryCode"))}";
                var response = await httpClient.GetAsync(BaseUrl + $"api/Batch/GetNewBatch?{query}");
                if (!response.IsSuccessStatusCode)
                {
                    if (response.StatusCode == HttpStatusCode.BadRequest
                        || response.StatusCode == HttpStatusCode.NotFound
                        || response.StatusCode == HttpStatusCode.Forbidden)
                    {
                        var errorMessage = await response.Content.ReadAsStringAsync();
                        throw new HttpRequestException(
                            $"{(int) response.StatusCode} {response.StatusCode.ToString()}: {errorMessage}");
                    }

                    response.EnsureSuccessStatusCode();
                }

                return JsonConvert.DeserializeObject<GetNewBatchResult>(await response.Content.ReadAsStringAsync());
            }
        }

        public async Task<UploadOutputResult> UploadOutputAsync(int inputId, OutputContent outputContent)
        {
            using (var httpClient = new HttpClient())
            {
                httpClient.DefaultRequestHeaders.UserAgent.Add(UserAgent);
                httpClient.DefaultRequestHeaders.Accept.Add(
                    new MediaTypeWithQualityHeaderValue("application/json"));
                var query = $"inputId={inputId}" +
                            $"&email={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:Email"))}";
                var response = await httpClient.PostAsJsonAsync(BaseUrl + $"api/Batch/UploadOutput?{query}", outputContent);
                if (!response.IsSuccessStatusCode)
                {
                    if (response.StatusCode == HttpStatusCode.BadRequest 
                        || response.StatusCode == HttpStatusCode.NotFound
                        || response.StatusCode == HttpStatusCode.Forbidden)
                    {
                        var errorMessage = await response.Content.ReadAsStringAsync();
                        throw new HttpRequestException($"{(int) response.StatusCode} {response.StatusCode.ToString()}: {errorMessage}");
                    }
                    response.EnsureSuccessStatusCode();
                }
                return JsonConvert.DeserializeObject<UploadOutputResult>(await response.Content.ReadAsStringAsync());
            }
        }

        public async Task CancelInputsAsync(string[] pendingFiles)
        {
            using (var httpClient = new HttpClient())
            {
                httpClient.DefaultRequestHeaders.UserAgent.Add(UserAgent);
                var query = $"email={UrlEncoder.Default.Encode(_configuration.GetValue<string>("BatchClient:Email"))}";
                var pendingInputs = pendingFiles.Select(pendingFile => Int32.Parse(System.IO.Path.GetFileName(pendingFile))).ToList();
                var response = await httpClient.PostAsJsonAsync(BaseUrl + $"api/Batch/CancelInputs?{query}", pendingInputs);
                if (!response.IsSuccessStatusCode)
                {
                    if (response.StatusCode == HttpStatusCode.BadRequest
                        || response.StatusCode == HttpStatusCode.NotFound
                        || response.StatusCode == HttpStatusCode.Forbidden)
                    {
                        var errorMessage = await response.Content.ReadAsStringAsync();
                        throw new HttpRequestException($"{(int)response.StatusCode} {response.StatusCode.ToString()}: {errorMessage}");
                    }
                    response.EnsureSuccessStatusCode();
                }                
            }
        }
    }
}
