using System;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    static void Main()
    {
        int max = 15_000_000; // Count prime numbers up to 15 million
        int totalPrimes = 0;

        // The built-in Parallel.For in C# uses the ThreadPool.
        // To avoid locks, we use the overload with thread-local variables.
        Parallel.For(1, max + 1, 
            () => 0, 
            (i, loopState, localCount) =>
            {
                if (IsPrime(i)) localCount++;
                return localCount;
            },
            localCount => Interlocked.Add(ref totalPrimes, localCount)
        );

        Console.WriteLine($"Total primes found: {totalPrimes}");
    }

    // The same naive algorithm for CPU load
    static bool IsPrime(int number)
    {
        if (number <= 1) return false;
        if (number == 2) return true;
        if (number % 2 == 0) return false;

        int boundary = (int)Math.Sqrt(number);
        for (int i = 3; i <= boundary; i += 2)
        {
            if (number % i == 0)
                return false;
        }
        return true;
    }
}