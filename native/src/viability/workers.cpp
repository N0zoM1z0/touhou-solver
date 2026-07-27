#include <algorithm>
#include <thread>

#include "src/internal/abi_impl.hpp"
#include "src/viability/workers.hpp"

namespace touhou_native::viability_internal {
namespace {

thread_local int viability_worker_limit = 4;

}  // namespace

int worker_count() {
    const unsigned hardware_threads = std::thread::hardware_concurrency();
    return std::max(
        1,
        std::min(
            viability_worker_limit,
            static_cast<int>(
                hardware_threads == 0 ? 1 : hardware_threads
            )
        )
    );
}

int set_worker_limit(int worker_limit) {
    if (worker_limit < 1 || worker_limit > 4) {
        return -1;
    }
    viability_worker_limit = worker_limit;
    return 0;
}

}  // namespace touhou_native::viability_internal

int touhou_native_impl_set_current_thread_viability_worker_limit_v1(
    int worker_limit
) {
    return touhou_native::viability_internal::set_worker_limit(worker_limit);
}
