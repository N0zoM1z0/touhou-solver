#pragma once

#if defined(_WIN32)
#define TOUHOU_EXPORT extern "C" __declspec(dllexport)
#else
#define TOUHOU_EXPORT \
    extern "C" __attribute__((visibility("default")))
#endif

