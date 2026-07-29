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

std::int32_t signed_dword(std::uint32_t bits) {
    std::int32_t value = 0;
    static_assert(sizeof(value) == sizeof(bits));
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

float x87_mul_store(float lhs, float rhs) {
    float result = 0.0F;
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
    __asm__ __volatile__(
        "flds %1\n\t"
        "fmuls %2\n\t"
        "fstps %0"
        : "=m"(result)
        : "m"(lhs), "m"(rhs)
    );
#else
    volatile float stored = lhs * rhs;
    result = stored;
#endif
    return result;
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

float x87_mul_add_store(float lhs, float rhs, float addend) {
    float result = 0.0F;
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
    __asm__ __volatile__(
        "flds %1\n\t"
        "fmuls %2\n\t"
        "fadds %3\n\t"
        "fstps %0"
        : "=m"(result)
        : "m"(lhs), "m"(rhs), "m"(addend)
    );
#else
    volatile float stored = lhs * rhs + addend;
    result = stored;
#endif
    return result;
}

float x87_elapsed_width_div_store(
    std::int32_t elapsed,
    float fraction,
    float width,
    std::int32_t divisor
) {
    float result = 0.0F;
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
    __asm__ __volatile__(
        "fildl %1\n\t"
        "fadds %2\n\t"
        "fmuls %3\n\t"
        "fidivl %4\n\t"
        "fstps %0"
        : "=m"(result)
        : "m"(elapsed), "m"(fraction), "m"(width), "m"(divisor)
    );
#else
    volatile float stored =
        (static_cast<float>(elapsed) + fraction) * width
        / static_cast<float>(divisor);
    result = stored;
#endif
    return result;
}

float x87_fade_width_store(
    std::int32_t elapsed,
    float fraction,
    float width,
    std::int32_t divisor
) {
    float result = 0.0F;
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
    __asm__ __volatile__(
        "fildl %1\n\t"
        "fadds %2\n\t"
        "fmuls %3\n\t"
        "fidivl %4\n\t"
        "fsubrs %3\n\t"
        "fstps %0"
        : "=m"(result)
        : "m"(elapsed), "m"(fraction), "m"(width), "m"(divisor)
    );
#else
    volatile float stored =
        width
        - (static_cast<float>(elapsed) + fraction) * width
            / static_cast<float>(divisor);
    result = stored;
#endif
    return result;
}

void print_words(
    const std::uint32_t* words,
    std::size_t count
) {
    for (std::size_t index = 0; index < count; ++index) {
        if (index) {
            std::cout << ' ';
        }
        std::cout << "0x" << std::hex << std::setfill('0') << std::setw(8)
                  << words[index];
    }
    std::cout << '\n';
}

void validate_finite(float value, const char* field) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(std::string(field) + " must be finite");
    }
}

int run_movement(int argc, char** argv) {
    if (argc != 12) {
        throw std::invalid_argument(
            "movement expects x y mask axis_x axis_y scale left top right bottom"
        );
    }
    float x = float_from_bits(parse_dword(argv[2]));
    float y = float_from_bits(parse_dword(argv[3]));
    const auto mask = parse_dword(argv[4]) & 0xFFFFU;
    const float axis_scale_x = float_from_bits(parse_dword(argv[5]));
    const float axis_scale_y = float_from_bits(parse_dword(argv[6]));
    const float scale = float_from_bits(parse_dword(argv[7]));
    const float left = float_from_bits(parse_dword(argv[8]));
    const float top = float_from_bits(parse_dword(argv[9]));
    const float right = float_from_bits(parse_dword(argv[10]));
    const float bottom = float_from_bits(parse_dword(argv[11]));
    for (const auto value : {
             x, y, axis_scale_x, axis_scale_y, scale,
             left, top, right, bottom,
         }) {
        validate_finite(value, "movement value");
    }
    if (
        axis_scale_x < 0.0F || axis_scale_y < 0.0F || scale < 0.0F
        || left > right || top > bottom
    ) {
        throw std::invalid_argument("invalid movement scale or bounds");
    }

    int axis_x = 0;
    int axis_y = 0;
    if ((mask & 0x50U) == 0x50U) {
        axis_x = -1;
        axis_y = -1;
    } else if ((mask & 0x60U) == 0x60U) {
        axis_x = -1;
        axis_y = 1;
    } else if ((mask & 0x90U) == 0x90U) {
        axis_x = 1;
        axis_y = -1;
    } else if ((mask & 0xA0U) == 0xA0U) {
        axis_x = 1;
        axis_y = 1;
    } else if (mask & 0x20U) {
        axis_y = 1;
    } else if (mask & 0x10U) {
        axis_y = -1;
    } else if (mask & 0x40U) {
        axis_x = -1;
    } else if (mask & 0x80U) {
        axis_x = 1;
    }

    const bool diagonal = axis_x != 0 && axis_y != 0;
    const bool focused = (mask & 0x04U) != 0;
    const float speed = float_from_bits(
        focused
            ? (diagonal ? 0x3FD02C18U : 0x40133333U)
            : (diagonal ? 0x403504F3U : 0x40800000U)
    );
    const float signed_x =
        axis_x == 0 ? 0.0F : (axis_x > 0 ? speed : -speed);
    const float signed_y =
        axis_y == 0 ? 0.0F : (axis_y > 0 ? speed : -speed);
    const float scaled_x = x87_mul_store(signed_x, axis_scale_x);
    const float scaled_y = x87_mul_store(signed_y, axis_scale_y);
    const float delta_x = x87_mul_store(scaled_x, scale);
    const float delta_y = x87_mul_store(scaled_y, scale);
    x = x87_add_store(x, delta_x);
    y = x87_add_store(y, delta_y);
    x = x < left ? left : (x > right ? right : x);
    y = y < top ? top : (y > bottom ? bottom : y);
    const std::uint32_t result[] = {
        bits_from_float(x),
        bits_from_float(y),
        bits_from_float(delta_x),
        bits_from_float(delta_y),
    };
    print_words(result, 4);
    return 0;
}

struct LaserState {
    float tail;
    float head;
    float maximum_length;
    float width;
    float current_width;
    float speed;
    std::int32_t warmup_frames;
    std::int32_t active_frames;
    std::int32_t fade_frames;
    std::int32_t collision_enable_frame;
    std::int32_t collision_disable_frame;
    std::uint32_t flags;
    std::uint32_t phase;
    std::uint32_t timer_bits;
    float timer_fraction;
    bool active;
};

void advance_timer(LaserState& state, float scale) {
    const float threshold = float_from_bits(0x3F7D70A4U);
    if (scale > threshold) {
        ++state.timer_bits;
        return;
    }
    state.timer_fraction = x87_add_store(state.timer_fraction, scale);
    if (state.timer_fraction >= 1.0F) {
        ++state.timer_bits;
        state.timer_fraction = x87_sub_store(state.timer_fraction, 1.0F);
    }
}

void add_check(
    std::uint32_t& code,
    std::uint32_t phase,
    bool graze
) {
    const auto count = code & 0xFU;
    const auto check = (phase & 3U) | (graze ? 4U : 0U);
    code |= check << (4U + count * 4U);
    code = (code & ~0xFU) | (count + 1U);
}

void cull_tail(LaserState& state) {
    if (state.tail >= 640.0F) {
        state.active = false;
    }
}

int run_laser(int argc, char** argv) {
    if (argc != 19) {
        throw std::invalid_argument(
            "laser expects tail head max width current speed warmup active_frames "
            "fade enable disable flags phase timer fraction active scale"
        );
    }
    LaserState state{
        float_from_bits(parse_dword(argv[2])),
        float_from_bits(parse_dword(argv[3])),
        float_from_bits(parse_dword(argv[4])),
        float_from_bits(parse_dword(argv[5])),
        float_from_bits(parse_dword(argv[6])),
        float_from_bits(parse_dword(argv[7])),
        signed_dword(parse_dword(argv[8])),
        signed_dword(parse_dword(argv[9])),
        signed_dword(parse_dword(argv[10])),
        signed_dword(parse_dword(argv[11])),
        signed_dword(parse_dword(argv[12])),
        parse_dword(argv[13]),
        parse_dword(argv[14]),
        parse_dword(argv[15]),
        float_from_bits(parse_dword(argv[16])),
        parse_dword(argv[17]) != 0,
    };
    const float scale = float_from_bits(parse_dword(argv[18]));
    for (const auto value : {
             state.tail, state.head, state.maximum_length, state.width,
             state.current_width, state.speed, state.timer_fraction, scale,
         }) {
        validate_finite(value, "laser value");
    }
    if (
        scale < 0.0F || state.phase > 2U
        || state.maximum_length < 0.0F || state.width < 0.0F
    ) {
        throw std::invalid_argument("invalid laser state or scale");
    }

    std::uint32_t checks_code = 0;
    if (state.active) {
        state.head = x87_mul_add_store(state.speed, scale, state.head);
        const long double visible =
            static_cast<long double>(state.head)
            - static_cast<long double>(state.tail);
        if (visible > static_cast<long double>(state.maximum_length)) {
            state.tail = x87_sub_store(state.head, state.maximum_length);
        }
        if (state.tail < 0.0F) {
            state.tail = 0.0F;
        }

        if (state.phase == 0U) {
            if ((state.flags & 1U) == 0) {
                const auto ramp_frames =
                    state.warmup_frames < 30 ? state.warmup_frames : 30;
                const auto ramp_start = state.warmup_frames - ramp_frames;
                if (ramp_start >= signed_dword(state.timer_bits)) {
                    state.current_width = float_from_bits(0x3F99999AU);
                } else if (state.warmup_frames != 0) {
                    state.current_width = x87_elapsed_width_div_store(
                        signed_dword(state.timer_bits),
                        state.timer_fraction,
                        state.width,
                        state.warmup_frames
                    );
                } else {
                    state.current_width = state.width;
                }
            }
            if (
                signed_dword(state.timer_bits)
                >= state.collision_enable_frame
            ) {
                add_check(checks_code, 0, false);
            }
            if (signed_dword(state.timer_bits) < state.warmup_frames) {
                advance_timer(state, scale);
                cull_tail(state);
                goto done;
            }
            state.phase = 1;
            state.timer_bits = 0;
            state.timer_fraction = 0.0F;
            state.current_width = state.width;
        }

        if (state.phase == 1U) {
            add_check(
                checks_code,
                1,
                signed_dword(state.timer_bits) % 20 == 0
            );
            if (signed_dword(state.timer_bits) < state.active_frames) {
                advance_timer(state, scale);
                cull_tail(state);
                goto done;
            }
            state.phase = 2;
            state.timer_bits = 0;
            state.timer_fraction = 0.0F;
            if (state.fade_frames == 0) {
                state.active = false;
                goto done;
            }
        }

        if ((state.flags & 1U) == 0) {
            state.current_width =
                state.fade_frames > 0
                    ? x87_fade_width_store(
                          signed_dword(state.timer_bits),
                          state.timer_fraction,
                          state.width,
                          state.fade_frames
                      )
                    : 0.0F;
            if (state.current_width < 0.0F) {
                state.current_width = 0.0F;
            }
        }
        if (
            signed_dword(state.timer_bits)
            < state.collision_disable_frame
        ) {
            add_check(checks_code, 2, false);
        }
        if (signed_dword(state.timer_bits) >= state.fade_frames) {
            state.active = false;
            goto done;
        }
        advance_timer(state, scale);
        cull_tail(state);
    }

done:
    const std::uint32_t result[] = {
        bits_from_float(state.tail),
        bits_from_float(state.head),
        bits_from_float(state.current_width),
        state.phase,
        state.timer_bits,
        bits_from_float(state.timer_fraction),
        state.active ? 1U : 0U,
        checks_code,
    };
    print_words(result, 8);
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (std::fesetround(FE_TONEAREST) != 0) {
            throw std::runtime_error("failed to select round-to-nearest");
        }
        if (argc < 2) {
            throw std::invalid_argument("expected movement or laser");
        }
        const std::string operation(argv[1]);
        if (operation == "movement") {
            return run_movement(argc, argv);
        }
        if (operation == "laser") {
            return run_laser(argc, argv);
        }
        throw std::invalid_argument("unknown operation");
    } catch (const std::exception& error) {
        std::cerr << "th08_scale_transition_probe: " << error.what() << '\n';
        return 2;
    }
}
