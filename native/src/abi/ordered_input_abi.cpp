#include "include/touhou_native/abi.h"
#include "include/touhou_native/export.hpp"
#include "src/internal/ordered_input_impl.hpp"


TOUHOU_EXPORT int touhou_async_ordered_input_issue_v1(
    const TouhouAsyncOrderedInputIssueQueryV1* query,
    TouhouAsyncOrderedInputIssueOutputV1* output
) {
    return touhou_native_impl_async_ordered_input_issue_v1(query, output);
}
