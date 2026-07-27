#pragma once

#include <cstdint>

namespace touhou_native {

struct PipelineLabel {
    std::uint16_t frames;
    float margin;
};

inline bool pipeline_label_less(
    const PipelineLabel& left,
    const PipelineLabel& right
) {
    return (
        left.frames < right.frames
        || (
            left.frames == right.frames
            && left.margin < right.margin
        )
    );
}

inline bool pipeline_label_equal(
    const PipelineLabel& left,
    const PipelineLabel& right
) {
    return left.frames == right.frames && left.margin == right.margin;
}

inline bool pipeline_label_less_equal(
    const PipelineLabel& left,
    const PipelineLabel& right
) {
    return (
        pipeline_label_less(left, right)
        || pipeline_label_equal(left, right)
    );
}

}  // namespace touhou_native

