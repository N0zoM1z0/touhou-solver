#pragma once

#include <algorithm>
#include <cmath>

struct SegmentGeometry {
    float start_x;
    float start_y;
    float vector_x;
    float vector_y;
    float length_squared;
    float min_x;
    float max_x;
    float min_y;
    float max_y;
};

inline SegmentGeometry segment_geometry(
    float origin_x,
    float origin_y,
    float angle,
    float tail,
    float head
) {
    const float cosine = std::cos(angle);
    const float sine = std::sin(angle);
    const float length = head - tail;
    const float vector_x = cosine * length;
    const float vector_y = sine * length;
    const float start_x = origin_x + cosine * tail;
    const float start_y = origin_y + sine * tail;
    const float end_x = start_x + vector_x;
    const float end_y = start_y + vector_y;
    return {
        start_x,
        start_y,
        vector_x,
        vector_y,
        vector_x * vector_x + vector_y * vector_y,
        std::min(start_x, end_x),
        std::max(start_x, end_x),
        std::min(start_y, end_y),
        std::max(start_y, end_y),
    };
}

inline float segment_clearance(
    float sample_x,
    float sample_y,
    const SegmentGeometry& segment,
    float occupied_radius
) {
    float projection = 0.0F;
    if (segment.length_squared > 1e-9F) {
        projection = (
            (sample_x - segment.start_x) * segment.vector_x
            + (sample_y - segment.start_y) * segment.vector_y
        ) / segment.length_squared;
        projection = std::min(1.0F, std::max(0.0F, projection));
    }
    const float closest_x = segment.start_x + projection * segment.vector_x;
    const float closest_y = segment.start_y + projection * segment.vector_y;
    return std::hypot(
        sample_x - closest_x,
        sample_y - closest_y
    ) - occupied_radius;
}

inline float segment_distance_squared(
    float sample_x,
    float sample_y,
    const SegmentGeometry& segment
) {
    float projection = 0.0F;
    if (segment.length_squared > 1e-9F) {
        projection = (
            (sample_x - segment.start_x) * segment.vector_x
            + (sample_y - segment.start_y) * segment.vector_y
        ) / segment.length_squared;
        projection = std::min(1.0F, std::max(0.0F, projection));
    }
    const float delta_x = (
        sample_x - (segment.start_x + projection * segment.vector_x)
    );
    const float delta_y = (
        sample_y - (segment.start_y + projection * segment.vector_y)
    );
    return delta_x * delta_x + delta_y * delta_y;
}
