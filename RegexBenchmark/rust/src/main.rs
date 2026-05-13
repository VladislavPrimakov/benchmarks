use regex::Regex;

fn main() {
    // In Rust, regexes are precompiled once, just like in other languages.
    let re = Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap();
    let text = "Please contact support@example.com or sales@example.org for more info.";

    let mut count = 0;

    // Loop the same 10 million times
    for _ in 0..10_000_000 {
        count += re.find_iter(text).count();
    }

    println!("Total matches: {}", count);
}
