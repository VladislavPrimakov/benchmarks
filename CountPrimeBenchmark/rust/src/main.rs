use rayon::prelude::*;

// Naive prime number checking algorithm (consumes maximum CPU)
fn is_prime(n: u32) -> bool {
    if n <= 1 { return false; }
    if n == 2 { return true; }
    if n % 2 == 0 { return false; }
    
    let limit = (n as f64).sqrt() as u32;
    let mut i = 3;
    while i <= limit {
        if n % i == 0 { return false; }
        i += 2;
    }
    true
}

fn main() {
    let max = 15_000_000; // Count prime numbers up to 15 million
    
    // .into_par_iter() instantly turns a standard iterator into a multi-threaded one,
    // the Rayon "Work-Stealing" algorithm will load cores at 100%
    let count: u32 = (1..=max)
        .into_par_iter()
        .filter(|&x| is_prime(x))
        .count() as u32;
    
    println!("Total primes found: {}", count);
}
