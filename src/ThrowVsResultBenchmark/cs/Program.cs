using System.Diagnostics;
using System.Runtime.CompilerServices;

var mode = args.Length > 0 ? args[0].ToLowerInvariant() : "result";
var errorPercent = args.Length > 1 ? int.Parse(args[1]) : 10;
var iterations = args.Length > 2 ? int.Parse(args[2]) : 3_000_000;

const int PatternLength = 1024;
var shouldFail = new bool[PatternLength];
uint state = 42;
for (var i = 0; i < PatternLength; i++) {
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    shouldFail[i] = (state % 100) < (uint)errorPercent;
}

var allocBefore = GC.GetAllocatedBytesForCurrentThread();
var sw = Stopwatch.StartNew();

var checksum = mode switch {
    "result" => RunResult(shouldFail, iterations),
    "tryout" => RunTryOut(shouldFail, iterations),
    "throw" => RunThrow(shouldFail, iterations),
    "async-result" => RunAsyncResult(shouldFail, iterations).GetAwaiter().GetResult(),
    "async-throw" => RunAsyncThrow(shouldFail, iterations).GetAwaiter().GetResult(),
    _ => throw new ArgumentException($"Unknown mode '{mode}'. Use: result | tryout | throw | async-result | async-throw")
};

sw.Stop();
var allocBytes = GC.GetAllocatedBytesForCurrentThread() - allocBefore;
Console.WriteLine($"Mode={mode} ErrorPercent={errorPercent}% Iterations={iterations} Time={sw.Elapsed.TotalMilliseconds:F2}ms Alloc={allocBytes:N0}B Checksum={checksum}");

static long RunResult(bool[] pattern, int iterations) {
    long sum = 0;
    const int mask = PatternLength - 1;
    for (var i = 0; i < iterations; i++) {
        sum += ExecuteResult(i, pattern[i & mask]) switch {
            int ok => ok,
            DomainError<ErrorCode> err => -(int)err.Code - err.Message.Length
        };
    }

    return sum;
}

static long RunTryOut(bool[] pattern, int iterations) {
    long sum = 0;
    const int mask = PatternLength - 1;
    for (var i = 0; i < iterations; i++) {
        sum += ExecuteTryOut(i, pattern[i & mask], out var ok, out var err, out var msg)
            ? ok
            : -(int)err - msg!.Length;
    }

    return sum;
}

static long RunThrow(bool[] pattern, int iterations) {
    long sum = 0;
    const int mask = PatternLength - 1;
    for (var i = 0; i < iterations; i++) {
        try {
            sum += ExecuteThrow(i, pattern[i & mask]);
        } catch (OpException ex) {
            sum -= (int)ex.Code + ex.Message.Length;
        }
    }

    return sum;
}

static async ValueTask<long> RunAsyncResult(bool[] pattern, int iterations) {
    long sum = 0;
    const int mask = PatternLength - 1;
    for (var i = 0; i < iterations; i++) {
        sum += await ExecuteResultAsync(i, pattern[i & mask]) switch {
            int ok => ok,
            DomainError<ErrorCode> err => -(int)err.Code - err.Message.Length
        };
    }

    return sum;
}

static async ValueTask<long> RunAsyncThrow(bool[] pattern, int iterations) {
    long sum = 0;
    const int mask = PatternLength - 1;
    for (var i = 0; i < iterations; i++) {
        try {
            sum += await ExecuteThrowAsync(i, pattern[i & mask]);
        } catch (OpException ex) {
            sum -= (int)ex.Code + ex.Message.Length;
        }
    }

    return sum;
}

[MethodImpl(MethodImplOptions.NoInlining)]
static Result<int, ErrorCode> ExecuteResult(int input, bool fail) =>
    fail
        ? new Result<int, ErrorCode>(new DomainError<ErrorCode>(ErrorCode.NotFound, "Shard not found."))
        : new Result<int, ErrorCode>((input * 3) + 1);

[MethodImpl(MethodImplOptions.NoInlining)]
static bool ExecuteTryOut(int input, bool fail, out int value, out ErrorCode error, out string? message) {
    if (fail) {
        value = 0;
        error = ErrorCode.NotFound;
        message = "Shard not found.";
        return false;
    }

    value = (input * 3) + 1;
    error = ErrorCode.None;
    message = null;
    return true;
}

[MethodImpl(MethodImplOptions.NoInlining)]
static int ExecuteThrow(int input, bool fail) =>
    fail
        ? throw new OpException(ErrorCode.NotFound, "Shard not found.")
        : (input * 3) + 1;

[MethodImpl(MethodImplOptions.NoInlining)]
static async ValueTask<Result<int, ErrorCode>> ExecuteResultAsync(int input, bool fail) {
    await ValueTask.CompletedTask;
    return fail
        ? new Result<int, ErrorCode>(new DomainError<ErrorCode>(ErrorCode.NotFound, "Shard not found."))
        : new Result<int, ErrorCode>((input * 3) + 1);
}

[MethodImpl(MethodImplOptions.NoInlining)]
static async ValueTask<int> ExecuteThrowAsync(int input, bool fail) {
    await ValueTask.CompletedTask;
    return fail
        ? throw new OpException(ErrorCode.NotFound, "Shard not found.")
        : (input * 3) + 1;
}

/// <summary>Domain error codes returned by the benchmark operations.</summary>
public enum ErrorCode : byte {
    None = 0,
    NotFound = 1,
    NotLeader = 2
}

/// <summary>Structured error value carried by <see cref="Result{TOk, TError}"/>.</summary>
public readonly record struct DomainError<TError>(TError Code, string Message)
    where TError : unmanaged, Enum;

/// <summary>Zero-boxing C# 15 stack union result.</summary>
[Union]
public readonly struct Result<TOk, TError> : IUnion
    where TError : unmanaged, Enum {
    private const byte StateOk = 1;
    private const byte StateError = 2;

    private readonly TOk _value;
    private readonly DomainError<TError> _error;
    private readonly byte _state;

    public Result(TOk value) {
        _value = value;
        _error = default;
        _state = StateOk;
    }

    public Result(DomainError<TError> error) {
        _value = default!;
        _error = error;
        _state = StateError;
    }

    public object? Value => _state switch {
        StateOk => _value,
        StateError => _error,
        _ => null
    };

    public bool HasValue => _state != 0;

    public bool TryGetValue(out TOk value) {
        value = _value;
        return _state == StateOk;
    }

    public bool TryGetValue(out DomainError<TError> error) {
        error = _error;
        return _state == StateError;
    }
}

/// <summary>Exception thrown on failure in the exception-based benchmark modes.</summary>
public sealed class OpException(ErrorCode code, string message) : Exception(message) {
    public ErrorCode Code { get; } = code;
}
