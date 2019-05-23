using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace GAB.Client.Models
{
    /// <summary>
    /// Represents an Input entity
    /// </summary>
    public class Input
    {
        /// <summary>
        /// Possible status of an input
        /// </summary>
        public enum InputStatusEnum
        {
            /// <summary>
            /// Ready to be processed
            /// </summary>
            Ready = 0,
            /// <summary>
            /// Being processed
            /// </summary>
            Processing = 1,
            /// <summary>
            /// Already processed
            /// </summary>
            Processed = 2,
            /// <summary>
            /// Error while processing
            /// </summary>
            Error = 3
        }

        /// <summary>
        /// Id of the input
        /// </summary>
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int InputId { get; set; }

        /// <summary>
        /// Parameters for the input (currently the filename)
        /// </summary>
        [MaxLength(800)]
        public string Parameters { get; set; }
    }
}
