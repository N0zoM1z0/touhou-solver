#include <cfenv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

float float_from_bits(std::uint32_t bits) {
    float value = 0.0F;
    static_assert(sizeof(value) == sizeof(bits));
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

std::uint32_t bits_from_float(float value) {
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

std::uint32_t parse_dword(const char* text) {
    std::size_t consumed = 0;
    const auto value = std::stoull(text, &consumed, 0);
    if (text[consumed] != '\0' || value > UINT32_MAX) {
        throw std::invalid_argument("expected one uint32 value");
    }
    return static_cast<std::uint32_t>(value);
}

float x87_add_store(float lhs, float rhs) {
    float result = 0.0F;
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
    __asm__ __volatile__(
        "flds %1\n\t"
        "fadds %2\n\t"
        "fstps %0"
        : "=m"(result)
        : "m"(lhs), "m"(rhs)
    );
#else
    volatile float stored = lhs + rhs;
    result = stored;
#endif
    return result;
}

float x87_sub_store(float lhs, float rhs) {
    float result = 0.0F;
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
    __asm__ __volatile__(
        "flds %1\n\t"
        "fsubs %2\n\t"
        "fstps %0"
        : "=m"(result)
        : "m"(lhs), "m"(rhs)
    );
#else
    volatile float stored = lhs - rhs;
    result = stored;
#endif
    return result;
}

void print_state(std::uint32_t elapsed_bits, std::uint32_t fraction_bits) {
    std::cout << "0x" << std::hex << std::setfill('0') << std::setw(8)
              << elapsed_bits << " 0x" << std::setw(8) << fraction_bits
              << '\n';
}

int run_advance(int argc, char** argv) {
    if (argc != 6) {
        throw std::invalid_argument(
            "advance expects elapsed_bits fraction_bits scale_bits ticks"
        );
    }
    auto elapsed_bits = parse_dword(argv[2]);
    auto fraction_bits = parse_dword(argv[3]);
    const auto scale_bits = parse_dword(argv[4]);
    const auto ticks = parse_dword(argv[5]);
    float fraction = float_from_bits(fraction_bits);
    const float scale = float_from_bits(scale_bits);
    const float threshold = float_from_bits(0x3F7D70A4U);
    if (!std::isfinite(fraction) || !std::isfinite(scale)) {
        throw std::invalid_argument("probe supports finite inputs only");
    }
    for (std::uint32_t tick = 0; tick < ticks; ++tick) {
        if (scale > threshold) {
            ++elapsed_bits;
            continue;
        }
        fraction = x87_add_store(fraction, scale);
        if (!std::isfinite(fraction)) {
            throw std::invalid_argument("probe transition became non-finite");
        }
        if (fraction >= 1.0F) {
            ++elapsed_bits;
            fraction = x87_sub_store(fraction, 1.0F);
        }
    }
    print_state(elapsed_bits, bits_from_float(fraction));
    return 0;
}

int run_branch(int argc, char** argv) {
    if (argc != 4) {
        throw std::invalid_argument("branch expects target_bits fraction_bits");
    }
    const auto target_bits = parse_dword(argv[2]);
    const auto fraction_bits = parse_dword(argv[3]);
    if (!std::isfinite(float_from_bits(fraction_bits))) {
        throw std::invalid_argument("probe supports finite fractions only");
    }
    print_state(target_bits, fraction_bits);
    return 0;
}

int run_reset(int argc, char** argv) {
    if (argc != 3) {
        throw std::invalid_argument("reset expects target_bits");
    }
    print_state(parse_dword(argv[2]), 0);
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (std::fesetround(FE_TONEAREST) != 0) {
            throw std::runtime_error("failed to select round-to-nearest");
        }
        if (argc < 2) {
            throw std::invalid_argument("expected advance, branch, or reset");
        }
        const std::string operation(argv[1]);
        if (operation == "advance") {
            return run_advance(argc, argv);
        }
        if (operation == "branch") {
            return run_branch(argc, argv);
        }
        if (operation == "reset") {
            return run_reset(argc, argv);
        }
        throw std::invalid_argument("unknown operation");
    } catch (const std::exception& error) {
        std::cerr << "th08_ecl_timer_probe: " << error.what() << '\n';
        return 2;
    }
}
