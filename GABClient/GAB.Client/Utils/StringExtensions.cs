using System.Text.RegularExpressions;

namespace GAB.Client.Utils
{
    public static class StringExtensions
    {
        public static string MaskEmailAddress(string email)
        {
            var pattern = @"(?<=[\w]{1})[\w-\._\+%]*(?=[\w]{1}@)";
            return Regex.Replace(email, pattern, m => new string('*', m.Length));
        }
    }
}
