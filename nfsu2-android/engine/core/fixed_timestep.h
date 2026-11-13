// Passo fixo de simulação com fator de interpolação para o renderer.
#pragma once

namespace nfsu2 {

class FixedTimestep {
public:
    explicit FixedTimestep(double stepSeconds = 1.0 / 120.0, double maxFrameSeconds = 0.25)
        : step_(stepSeconds), maxFrame_(maxFrameSeconds) {}

    // Acumula o tempo do quadro e devolve quantos passos fixos devem rodar.
    int advance(double frameSeconds) {
        if (frameSeconds < 0.0) frameSeconds = 0.0;
        if (frameSeconds > maxFrame_) frameSeconds = maxFrame_;  // evita espiral da morte
        acc_ += frameSeconds;
        // Divisao com tolerancia: subtrair 'step_' em laco perde passos por erro de ponto flutuante.
        int n = static_cast<int>(acc_ / step_ + 1e-9);
        acc_ -= n * step_;
        if (acc_ < 0.0) acc_ = 0.0;
        totalSteps_ += n;
        return n;
    }

    // Fração [0,1) entre o último passo e o próximo, para interpolar a renderização.
    double alpha() const { return acc_ / step_; }
    double step() const { return step_; }
    long long totalSteps() const { return totalSteps_; }

private:
    double step_;
    double maxFrame_;
    double acc_ = 0.0;
    long long totalSteps_ = 0;
};

}  // namespace nfsu2
