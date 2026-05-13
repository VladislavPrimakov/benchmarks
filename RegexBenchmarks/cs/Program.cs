using System;
using System.Text.RegularExpressions;

class Program
{
    static void Main()
    {
        string text = "Please contact support@example.com or sales@example.org for more info.";
        int count = 0;

        for (int i = 0; i < 10_000_000; i++)
        {
            count += MyRegex.Email().Count(text);
        }

        Console.WriteLine($"Total matches: {count}");
    }
}

internal partial class MyRegex {
    [GeneratedRegex(@"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")]
    public static partial Regex Email();
}