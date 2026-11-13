#include <cmath>

#include "check.h"
#include "core/fixed_timestep.h"

int main() {
    using nfsu2::FixedTimestep;

    // Independencia da taxa de quadros: 1 s simulado a 30, 60 e 144 FPS => mesmo numero de passos (+-1).
    const double rates[] = {30.0, 60.0, 144.0, 17.0};
    for (double fps : rates) {
        FixedTimestep t(1.0 / 120.0);
        const int frames = int(fps);
        for (int i = 0; i < frames; ++i) t.advance(1.0 / fps);
        CHECK(std::llabs(t.totalSteps() - 120) <= 1);
    }

    // Limite de quadro longo (evita espiral da morte).
    FixedTimestep t(0.01, 0.25);
    CHECK(t.advance(10.0) == 25);

    // Alfa de interpolacao fica em [0,1).
    FixedTimestep a(0.01);
    a.advance(0.015);
    CHECK(a.alpha() >= 0.0 && a.alpha() < 1.0);
    CHECK(std::fabs(a.alpha() - 0.5) < 1e-9);

    // Tempo negativo eh ignorado.
    FixedTimestep n(0.01);
    CHECK(n.advance(-1.0) == 0);

    TEST_MAIN_END();
}
