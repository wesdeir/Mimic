#pragma once

#include <cmath>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

// Shared helpers for the Phase 1 parity suite: load a one-column CSV of
// delay_ms values (golden files from tools/python_reference/golden/, or
// click_data/*.csv) and compute basic moments.

namespace mimic::test {

struct Moments {
    double mean = 0.0;
    double stdDev = 0.0;
    double min = 0.0;
    double max = 0.0;
    std::size_t count = 0;
};

inline std::vector<double> loadDelayColumn(const std::string& path, const std::string& columnName) {
    std::ifstream in(path);
    std::vector<double> out;
    if (!in) return out;

    std::string header;
    std::getline(in, header);
    std::vector<std::string> cols;
    {
        std::stringstream ss(header);
        std::string cell;
        while (std::getline(ss, cell, ',')) cols.push_back(cell);
    }
    int colIndex = -1;
    for (std::size_t i = 0; i < cols.size(); ++i) {
        if (cols[i] == columnName) {
            colIndex = static_cast<int>(i);
            break;
        }
    }
    if (colIndex < 0) return out;

    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string cell;
        int i = 0;
        while (std::getline(ss, cell, ',')) {
            if (i == colIndex) {
                try {
                    out.push_back(std::stod(cell));
                } catch (...) {
                }
                break;
            }
            ++i;
        }
    }
    return out;
}

inline Moments computeMoments(const std::vector<double>& values) {
    Moments m;
    m.count = values.size();
    if (values.empty()) return m;

    double sum = 0.0;
    m.min = values[0];
    m.max = values[0];
    for (double v : values) {
        sum += v;
        m.min = std::min(m.min, v);
        m.max = std::max(m.max, v);
    }
    m.mean = sum / static_cast<double>(values.size());

    double sqSum = 0.0;
    for (double v : values) sqSum += (v - m.mean) * (v - m.mean);
    m.stdDev = std::sqrt(sqSum / static_cast<double>(values.size()));
    return m;
}

inline double relativeDiff(double a, double b) {
    if (b == 0.0) return a == 0.0 ? 0.0 : 1.0;
    return std::abs(a - b) / std::abs(b);
}

} // namespace mimic::test
