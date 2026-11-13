// Micro-framework de testes (sem dependencias externas).
#pragma once
#include <cstdio>
#include <cstdlib>

static int g_failures = 0;

#define CHECK(cond)                                                              \
    do {                                                                         \
        if (!(cond)) {                                                           \
            std::fprintf(stderr, "FALHOU %s:%d: %s\n", __FILE__, __LINE__, #cond); \
            ++g_failures;                                                        \
        }                                                                        \
    } while (0)

#define TEST_MAIN_END()                                         \
    do {                                                        \
        if (g_failures) {                                       \
            std::fprintf(stderr, "%d falha(s)\n", g_failures);  \
            return 1;                                           \
        }                                                       \
        std::puts("OK");                                        \
        return 0;                                               \
    } while (0)
