use rayon::prelude::*;

// Наивный алгоритм проверки числа на простоту (съедает максимум CPU)
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
    let max = 15_000_000; // Считаем простые числа до 15 миллионов
    
    // .into_par_iter() мгновенно превращает обычный цикл в многопоточный,
    // алгоритм Rayon "Work-Stealing" загрузит ядра на 100%
    let count: u32 = (1..=max)
        .into_par_iter()
        .filter(|&x| is_prime(x))
        .count() as u32;
    
    println!("Total primes found: {}", count);
}
