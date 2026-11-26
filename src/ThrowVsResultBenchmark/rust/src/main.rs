use std::future::Future;
use std::hint::black_box;
use std::panic::{self, AssertUnwindSafe};
use std::pin::pin;
use std::task::{Context, Poll, RawWaker, RawWakerVTable, Waker};
use std::time::Instant;

const PATTERN_LENGTH: usize = 1024;
const PATTERN_MASK: usize = PATTERN_LENGTH - 1;

#[repr(u8)]
#[derive(Clone, Copy)]
enum ErrorCode {
    NotFound = 1,
}

struct DomainError {
    code: ErrorCode,
    message: &'static str,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("result");
    let error_percent: u32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(10);
    let iterations: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(3_000_000);

    let mut should_fail = [false; PATTERN_LENGTH];
    let mut state: u32 = 42;
    for slot in &mut should_fail {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        *slot = (state % 100) < error_percent;
    }

    let start = Instant::now();
    let checksum = match mode {
        "result" => run_result(&should_fail, iterations),
        "async-result" => block_on(run_async_result(&should_fail, iterations)),
        "panic" => run_panic(&should_fail, iterations),
        _ => panic!("Unknown mode '{mode}'. Use: result | async-result | panic"),
    };
    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;

    println!(
        "Mode={mode} ErrorPercent={error_percent}% Iterations={iterations} Time={elapsed_ms:.2}ms Checksum={checksum}"
    );
}

fn run_result(pattern: &[bool; PATTERN_LENGTH], iterations: usize) -> i64 {
    let pattern = black_box(pattern);
    let mut sum: i64 = 0;
    for i in 0..iterations {
        sum += match execute_result(black_box(i as i32), black_box(pattern[i & PATTERN_MASK])) {
            Ok(ok) => ok as i64,
            Err(err) => -(err.code as i64) - (err.message.len() as i64),
        };
    }
    black_box(sum)
}

async fn run_async_result(pattern: &[bool; PATTERN_LENGTH], iterations: usize) -> i64 {
    let pattern = black_box(pattern);
    let mut sum: i64 = 0;
    for i in 0..iterations {
        sum += match execute_result_async(black_box(i as i32), black_box(pattern[i & PATTERN_MASK])).await {
            Ok(ok) => ok as i64,
            Err(err) => -(err.code as i64) - (err.message.len() as i64),
        };
    }
    black_box(sum)
}

fn run_panic(pattern: &[bool; PATTERN_LENGTH], iterations: usize) -> i64 {
    panic::set_hook(Box::new(|_| {}));
    let pattern = black_box(pattern);
    let mut sum: i64 = 0;
    for i in 0..iterations {
        let input = black_box(i as i32);
        let fail = black_box(pattern[i & PATTERN_MASK]);
        match panic::catch_unwind(AssertUnwindSafe(|| execute_panic(input, fail))) {
            Ok(ok) => sum += ok as i64,
            Err(payload) => {
                if let Some(err) = payload.downcast_ref::<DomainError>() {
                    sum -= (err.code as i64) + (err.message.len() as i64);
                }
            }
        }
    }
    black_box(sum)
}

#[inline(never)]
fn execute_result(input: i32, fail: bool) -> Result<i32, DomainError> {
    if fail {
        Err(DomainError {
            code: ErrorCode::NotFound,
            message: "Shard not found.",
        })
    } else {
        Ok(input.wrapping_mul(3).wrapping_add(1))
    }
}

#[inline(never)]
async fn execute_result_async(input: i32, fail: bool) -> Result<i32, DomainError> {
    std::future::ready(()).await;
    execute_result(input, fail)
}

#[inline(never)]
fn execute_panic(input: i32, fail: bool) -> i32 {
    if fail {
        panic::panic_any(DomainError {
            code: ErrorCode::NotFound,
            message: "Shard not found.",
        });
    }
    input.wrapping_mul(3).wrapping_add(1)
}

fn block_on<F: Future>(fut: F) -> F::Output {
    fn noop_clone(_: *const ()) -> RawWaker {
        noop_raw_waker()
    }
    fn noop(_: *const ()) {}
    fn noop_raw_waker() -> RawWaker {
        const VTABLE: RawWakerVTable = RawWakerVTable::new(noop_clone, noop, noop, noop);
        RawWaker::new(std::ptr::null(), &VTABLE)
    }

    let waker = unsafe { Waker::from_raw(noop_raw_waker()) };
    let mut cx = Context::from_waker(&waker);
    let mut fut = pin!(fut);
    loop {
        if let Poll::Ready(out) = fut.as_mut().poll(&mut cx) {
            return out;
        }
    }
}
