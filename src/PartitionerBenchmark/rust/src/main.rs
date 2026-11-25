use std::mem::MaybeUninit;
use rayon::prelude::*;

const LENGTH: usize = 50_000_000;
const ITERATIONS: usize = 80;

fn main() {
    let mut arr: Vec<f32> = Vec::with_capacity(LENGTH);
    let chunk_size = LENGTH.div_ceil(rayon::current_num_threads());

    arr.spare_capacity_mut()[..LENGTH]
        .par_chunks_mut(chunk_size)
        .for_each(|chunk| {
            chunk.fill(MaybeUninit::new(16.0_f32));
        });

    // SAFETY: Every element in 0..LENGTH was initialized above.
    unsafe {
        arr.set_len(LENGTH);
    }

    for _ in 0..ITERATIONS {
        arr.par_chunks_mut(chunk_size).for_each(|chunk| {
            for x in chunk {
                *x = x.sqrt();
            }
        });
    }

    println!("First: {}, Last: {}", arr[0], arr[arr.len() - 1]);
}
