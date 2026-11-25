use std::hint::black_box;
use std::time::Instant;

const LENGTH: usize = 4096;

#[repr(C)]
#[derive(Clone, Copy)]
struct Item {
    #[allow(dead_code)]
    id: i32,
    value: i32,
    weight: i32,
    flags: i32,
}

fn next_u32(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}

fn create_items(length: usize) -> Vec<Item> {
    let mut items = Vec::with_capacity(length);
    let mut state: u32 = 42;
    for i in 0..length {
        let value = (next_u32(&mut state) % 1000) as i32;
        let weight = (next_u32(&mut state) % 64) as i32 + 1;
        let flags = next_u32(&mut state) as i32;
        items.push(Item {
            id: i as i32,
            value,
            weight,
            flags,
        });
    }
    items
}

#[inline(never)]
fn pass_sum(items: &[Item]) -> i64 {
    items
        .iter()
        .map(|x| (x.value as i64) * (x.weight as i64) + ((x.flags & 0xFF) as i64))
        .sum()
}

#[inline(never)]
fn pass_pipeline(items: &[Item]) -> i64 {
    items
        .iter()
        .filter(|x| (x.flags & 1) == 0)
        .map(|x| (x.value as i64) * (x.weight as i64) + ((x.flags & 0xFF) as i64))
        .sum()
}

fn run_sum(items: &[Item], iterations: usize) -> i64 {
    let mut total: i64 = 0;
    for _ in 0..iterations {
        total += black_box(pass_sum(black_box(items)));
    }
    total
}

fn run_pipeline(items: &[Item], iterations: usize) -> i64 {
    let mut total: i64 = 0;
    for _ in 0..iterations {
        total += black_box(pass_pipeline(black_box(items)));
    }
    total
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("sum");
    let iterations: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(200_000);

    let items = create_items(LENGTH);

    let start = Instant::now();
    let checksum = match mode {
        "sum" => run_sum(&items, iterations),
        "pipeline" => run_pipeline(&items, iterations),
        _ => panic!("Unknown mode '{mode}'. Use: sum | pipeline"),
    };
    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;

    println!(
        "Mode={mode} Length={LENGTH} Iterations={iterations} Time={elapsed_ms:.2}ms Checksum={checksum}"
    );
}
