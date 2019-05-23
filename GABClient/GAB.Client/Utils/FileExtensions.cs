using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace GAB.Client.Utils
{
    public static class FileExtensions
    {
        public static string Tail(string path, Int64 numberOfLines = 100)
        {
            return ReadEndTokens(path, numberOfLines, Encoding.UTF8, "\n");
        }


        // Get last 10 lines of very large text file 
        // https://stackoverflow.com/questions/398378/get-last-10-lines-of-very-large-text-file-10gb
        public static string ReadEndTokens(string path, Int64 numberOfTokens, Encoding encoding, string tokenSeparator)
        {

            int sizeOfChar = encoding.GetByteCount("\n");
            byte[] buffer = encoding.GetBytes(tokenSeparator);


            using (FileStream fs = new FileStream(path, FileMode.Open))
            {
                Int64 tokenCount = 0;
                Int64 endPosition = fs.Length / sizeOfChar;

                for (Int64 position = sizeOfChar; position < endPosition; position += sizeOfChar)
                {
                    fs.Seek(-position, SeekOrigin.End);
                    fs.Read(buffer, 0, buffer.Length);

                    if (encoding.GetString(buffer) == tokenSeparator)
                    {
                        tokenCount++;
                        if (tokenCount == numberOfTokens)
                        {
                            byte[] returnBuffer = new byte[fs.Length - fs.Position];
                            fs.Read(returnBuffer, 0, returnBuffer.Length);
                            return encoding.GetString(returnBuffer);
                        }
                    }
                }

                // handle case where number of tokens in file is less than numberOfTokens
                fs.Seek(0, SeekOrigin.Begin);
                buffer = new byte[fs.Length];
                fs.Read(buffer, 0, buffer.Length);
                return encoding.GetString(buffer);
            }
        }
    }
}
