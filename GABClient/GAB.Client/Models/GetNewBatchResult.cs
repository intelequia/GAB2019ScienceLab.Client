using System;
using System.Collections.Generic;

namespace GAB.Client.Models
{
    /// <summary>
    /// Represents an element from the Outputs Uploads
    /// </summary>
    public class OutputResult
    {
        /// <summary>
        /// The batch Id
        /// </summary>
        public Guid BatchId { get; set; }
        /// <summary>
        /// The Input id for the upload Uri
        /// </summary>
        public int InputId { get; set; }
        /// <summary>
        /// Light curves upload uris
        /// </summary>
        public string LightCurvesUploadUri { get; set; }

    }
    /// <summary>
    /// Represents the ouput of the GetNewBatch method
    /// </summary>
    public class GetNewBatchResult
    {
        /// <summary>
        /// The batch Id
        /// </summary>
        public Guid BatchId { get; set; }
        /// <summary>
        /// The list of inputs of this batch
        /// </summary>
        public List<Input> Inputs { get; set; }

        /// <summary>
        /// List of light curve upload uris
        /// </summary>
        public List<OutputResult> Outputs { get; set; }

    }
}
