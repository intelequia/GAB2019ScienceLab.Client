using System.Collections.Generic;
using Newtonsoft.Json;

namespace GAB.Client.Models
{
    /// <summary>
    /// Class representing the output content
    /// </summary>
    public class OutputContent
    {
        /// <summary>
        /// InputId
        /// </summary>
        public int inputid { get; set; }

        /// <summary>
        /// Container ID
        /// </summary>
        public string containerid { get; set; }

        /// <summary>
        /// Client version
        /// </summary>
        public string clientversion { get; set; }
        /// <summary>
        /// Target ID
        /// </summary>
        public string ticid { get; set; }

        /// <summary>
        /// Sector
        /// </summary>
        public int sector { get; set; }

        /// <summary>
        /// Camera
        /// </summary>
        public int camera { get; set; }

        /// <summary>
        /// CCD
        /// </summary>
        public int ccd { get; set; }

        /// <summary>
        /// RA
        /// </summary>
        public double ra { get; set; }

        /// <summary>
        /// DEC
        /// </summary>
        public double dec { get; set; }

        /// <summary>
        /// TESS Magnitude
        /// </summary>
        public double tmag { get; set; }
        /// <summary>
        /// Light curve filename
        /// </summary>
        public string lc { get; set; }
        /// <summary>
        /// Is a planet?
        /// </summary>
        public double isplanet { get; set; }

        /// <summary>
        /// Is not a planet?
        /// </summary>
        public double isnotplanet { get; set; }

        /// <summary>
        /// Probability
        /// </summary>
        public List<double> frequencies { get; set; }
    }
}
