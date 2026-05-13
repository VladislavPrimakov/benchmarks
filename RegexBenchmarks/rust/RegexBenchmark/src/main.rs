use regex::Regex;

fn main() {
    // В Rust регулярные выражения прекомпилируются один раз, как и в других языках.
    let re = Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap();
    let text = "Please contact support@example.com or sales@example.org for more info.";

    let mut count = 0;

    // Крутим те же 10 миллионов раз
    for _ in 0..10_000_000 {
        count += re.find_iter(text).count();
    }

    println!("Total matches: {}", count);
}
