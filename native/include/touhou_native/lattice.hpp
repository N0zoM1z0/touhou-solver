#pragma once

#include <cstddef>

namespace touhou_native {

inline std::size_t state_index(
    int layer,
    int action,
    int row,
    int column,
    int action_count,
    int row_count,
    int column_count
) {
    return (
        (
            static_cast<std::size_t>(layer) * action_count
            + static_cast<std::size_t>(action)
        )
        * row_count
        + static_cast<std::size_t>(row)
    )
        * column_count
        + static_cast<std::size_t>(column);
}

inline std::size_t action_value_index(
    int layer,
    int active,
    int selected,
    int row,
    int column,
    int action_count,
    int row_count,
    int column_count
) {
    return (
        (
            (
                (
                    static_cast<std::size_t>(layer) * action_count
                    + static_cast<std::size_t>(active)
                )
                * action_count
                + static_cast<std::size_t>(selected)
            )
            * row_count
            + static_cast<std::size_t>(row)
        )
        * column_count
        + static_cast<std::size_t>(column)
    );
}

inline std::size_t clearance_index(
    int frame,
    int row,
    int column,
    int row_count,
    int column_count
) {
    return (
        static_cast<std::size_t>(frame) * row_count
        + static_cast<std::size_t>(row)
    )
        * column_count
        + static_cast<std::size_t>(column);
}

struct Sample {
    int row;
    int column;
    double error;
    bool inside;
};

}  // namespace touhou_native

