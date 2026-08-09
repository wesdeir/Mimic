#pragma once

#include <cstddef>
#include <vector>

// Fixed-capacity ring buffer replacing Python's collections.deque(maxlen=N)
// used throughout engine.py (click_history, recent_click_times, all_delays,
// cps_history/cps_timestamps). Avoids per-push heap churn a std::deque with
// manual eviction would have, without pulling in boost::circular_buffer for
// a ~30-line feature.

namespace mimic::core::engine {

template <typename T>
class RingBuffer {
public:
    explicit RingBuffer(std::size_t capacity) : data_(capacity) {}

    void push(const T& value) {
        if (size_ < data_.size()) {
            data_[(start_ + size_) % data_.size()] = value;
            ++size_;
        } else {
            data_[start_] = value;
            start_ = (start_ + 1) % data_.size();
        }
    }

    std::size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    std::size_t capacity() const { return data_.size(); }

    const T& operator[](std::size_t i) const { return data_[(start_ + i) % data_.size()]; }
    const T& front() const { return data_[start_]; }
    const T& back() const { return data_[(start_ + size_ - 1) % data_.size()]; }

    // Copies the last n elements (or all, if size() < n) out in chronological
    // order -- used for click_history's "last 10" CPS window etc.
    std::vector<T> lastN(std::size_t n) const {
        std::size_t count = n < size_ ? n : size_;
        std::vector<T> out;
        out.reserve(count);
        for (std::size_t i = size_ - count; i < size_; ++i) {
            out.push_back((*this)[i]);
        }
        return out;
    }

    std::vector<T> toVector() const { return lastN(size_); }

    void popFront() {
        if (size_ > 0) {
            start_ = (start_ + 1) % data_.size();
            --size_;
        }
    }

private:
    std::vector<T> data_;
    std::size_t start_ = 0;
    std::size_t size_ = 0;
};

} // namespace mimic::core::engine
