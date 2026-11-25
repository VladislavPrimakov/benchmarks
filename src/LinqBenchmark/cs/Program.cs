using System.Diagnostics;
using System.Runtime.CompilerServices;

var mode = args.Length > 0 ? args[0].ToLowerInvariant() : "linq-sum";
var iterations = args.Length > 1 ? int.Parse(args[1]) : 200_000;

const int Length = 4096;
var items = CreateItems(Length);

var allocBefore = GC.GetAllocatedBytesForCurrentThread();
var sw = Stopwatch.StartNew();

var checksum = mode switch {
    "linq-sum" => RunLinqSum(items, iterations),
    "functor-sum" => RunFunctorSum(items, iterations),
    "linq-pipeline" => RunLinqPipeline(items, iterations),
    "functor-pipeline" => RunFunctorPipeline(items, iterations),
    _ => throw new ArgumentException($"Unknown mode '{mode}'. Use: linq-sum | functor-sum | linq-pipeline | functor-pipeline")
};

sw.Stop();
var allocBytes = GC.GetAllocatedBytesForCurrentThread() - allocBefore;
Console.WriteLine($"Mode={mode} Length={Length} Iterations={iterations} Time={sw.Elapsed.TotalMilliseconds:F2}ms Alloc={allocBytes:N0}B Checksum={checksum}");

static Item[] CreateItems(int length) {
    var items = new Item[length];
    uint state = 42;
    for (var i = 0; i < length; i++) {
        var value = (int)(NextUInt(ref state) % 1000);
        var weight = (int)(NextUInt(ref state) % 64) + 1;
        var flags = (int)NextUInt(ref state);
        items[i] = new Item(i, value, weight, flags);
    }

    return items;
}

static uint NextUInt(ref uint state) {
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    return state;
}

static long RunLinqSum(Item[] items, int iterations) {
    long total = 0;
    for (var i = 0; i < iterations; i++) {
        total += PassLinqSum(items);
    }

    return total;
}

static long RunFunctorSum(Item[] items, int iterations) {
    long total = 0;
    for (var i = 0; i < iterations; i++) {
        total += PassFunctorSum(items);
    }

    return total;
}

static long RunLinqPipeline(Item[] items, int iterations) {
    long total = 0;
    for (var i = 0; i < iterations; i++) {
        total += PassLinqPipeline(items);
    }

    return total;
}

static long RunFunctorPipeline(Item[] items, int iterations) {
    long total = 0;
    for (var i = 0; i < iterations; i++) {
        total += PassFunctorPipeline(items);
    }

    return total;
}

[MethodImpl(MethodImplOptions.NoInlining)]
static long PassLinqSum(Item[] items) =>
    items.Sum(static x => ((long)x.Value * x.Weight) + (x.Flags & 0xFF));

[MethodImpl(MethodImplOptions.NoInlining)]
static long PassFunctorSum(Item[] items) =>
    SumWithFunctor(items.AsSpan(), default(ItemValueSelector));

[MethodImpl(MethodImplOptions.NoInlining)]
static long PassLinqPipeline(Item[] items) =>
    items
        .Where(static x => (x.Flags & 1) == 0)
        .Select(static x => ((long)x.Value * x.Weight) + (x.Flags & 0xFF))
        .Sum();

[MethodImpl(MethodImplOptions.NoInlining)]
static long PassFunctorPipeline(Item[] items) =>
    FilterMapSumWithFunctor(items.AsSpan(), default(EvenFlagsPredicate), default(ItemValueSelector));

static long SumWithFunctor<T, TSelector>(ReadOnlySpan<T> span, TSelector selector)
    where TSelector : struct, ISelector<T, long> {
    long sum = 0;
    for (var i = 0; i < span.Length; i++) {
        sum += selector.Invoke(in span[i]);
    }

    return sum;
}

static long FilterMapSumWithFunctor<T, TPredicate, TSelector>(
    ReadOnlySpan<T> span,
    TPredicate predicate,
    TSelector selector)
    where TPredicate : struct, IPredicate<T>
    where TSelector : struct, ISelector<T, long> {
    long sum = 0;
    for (var i = 0; i < span.Length; i++) {
        ref readonly var item = ref span[i];
        if (predicate.Invoke(in item)) {
            sum += selector.Invoke(in item);
        }
    }

    return sum;
}

public readonly record struct Item(int Id, int Value, int Weight, int Flags);

public interface ISelector<T, out TResult> {
    TResult Invoke(in T item);
}

public interface IPredicate<T> {
    bool Invoke(in T item);
}

public readonly struct ItemValueSelector : ISelector<Item, long> {
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public long Invoke(in Item x) => ((long)x.Value * x.Weight) + (x.Flags & 0xFF);
}

public readonly struct EvenFlagsPredicate : IPredicate<Item> {
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public bool Invoke(in Item x) => (x.Flags & 1) == 0;
}
