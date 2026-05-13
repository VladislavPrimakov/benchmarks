using System;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    static void Main()
    {
        int max = 15_000_000; // Считаем те же простые числа до 15 миллионов
        int totalPrimes = 0;

        // Встроенный Parallel.For в C# использует ThreadPool.
        // Чтобы избежать блокировок (lock), мы используем перегрузку с локальными переменными потока
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

    // Тот же самый наивный алгоритм для нагрузки ядер CPU
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