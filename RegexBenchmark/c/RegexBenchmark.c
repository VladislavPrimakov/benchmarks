#include <stdio.h>
#include <string.h>
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>

int main(int argc, char ** argv) {
    // Our usual regex and text
    PCRE2_SPTR pattern = (unsigned char *)"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}";
    unsigned char subject[] = "Please contact support@example.com or sales@example.org for more info.";
    size_t len_subject = strlen((const char *)subject);

    int errornumber;
    PCRE2_SIZE erroroffset;

    // 1. First, compile the pattern into the internal PCRE2 format
    pcre2_code *re = pcre2_compile(
        pattern, PCRE2_ZERO_TERMINATED, 0,
        &errornumber, &erroroffset, NULL);

    if (re == NULL) {
        printf("Compilation failed\n");
        return 1;
    }

    // 2. MAGICKA: Instruct the JIT compiler to translate the regex into "bare" CPU machine instructions!
    pcre2_jit_compile(re, PCRE2_JIT_COMPLETE);

    pcre2_match_data *match_data = pcre2_match_data_create_from_pattern(re, NULL);

    int count = 0;
    
    // 3. Loop the same 10 million times
    for (int i = 0; i < 10000000; i++) {
        PCRE2_SIZE start_offset = 0;
        
        // Find all matches in the string (there are two in the text)
        while (start_offset < len_subject) {
            int rc = pcre2_match(
                re, subject, len_subject, start_offset, 0, match_data, NULL);
            
            if (rc < 0) break; // If there are no more matches, exit
            
            count++;
            
            // Move the "cursor" to the end of the match just found, to search further
            PCRE2_SIZE *ovector = pcre2_get_ovector_pointer(match_data);
            start_offset = ovector[1]; 
        }
    }

    printf("Total matches: %d\n", count);

    // Clean up memory, as is common in C
    pcre2_match_data_free(match_data);
    pcre2_code_free(re);

    return 0;
}
