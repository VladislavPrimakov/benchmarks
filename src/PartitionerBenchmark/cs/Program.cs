using System;
using System.Collections.Concurrent;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

const int Length = 50_000_000;
const int Iterations = 80;

float[] arr = GC.AllocateUninitializedArray<float>(Length);

int threads = Environment.ProcessorCount;
int chunkSize = (arr.Length + threads - 1) / threads;
var partitioner = Partitioner.Create(0, arr.Length, chunkSize);

Parallel.ForEach(partitioner, range =>
{
    arr.AsSpan(range.Item1, range.Item2 - range.Item1).Fill(16.0f);
});

for (int iter = 0; iter < Iterations; iter++)
{
    Parallel.ForEach(partitioner, range =>
    {
        Span<float> slice = arr.AsSpan(range.Item1, range.Item2 - range.Item1);

        Span<Vector<float>> vectors = MemoryMarshal.Cast<float, Vector<float>>(slice);

        for (int i = 0; i < vectors.Length; i++)
        {
            vectors[i] = Vector.SquareRoot(vectors[i]);
        }

        int remainderStart = vectors.Length * Vector<float>.Count;
        for (int i = remainderStart; i < slice.Length; i++)
        {
            slice[i] = MathF.Sqrt(slice[i]);
        }
    });
}

Console.WriteLine($"First: {arr[0]}, Last: {arr[^1]}");
