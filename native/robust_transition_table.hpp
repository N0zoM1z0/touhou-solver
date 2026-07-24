#pragma once

// Included inside the kernel's anonymous namespace.  The surrounding
// translation unit supplies Sample and the standard-library headers.

struct TransitionTable {
    double x_start;
    double x_step;
    int column_count;
    double y_start;
    double y_step;
    int row_count;
    std::vector<double> velocity_x;
    std::vector<double> velocity_y;
    int frames_per_layer;
    bool clamp_to_bounds;
    // Regular-lattice movement is separable. Caching one full 2-D sample for
    // every state repeats the same x transition for every row and the same y
    // transition for every column. Keep the axes independently and
    // reconstruct the Cartesian sample in the recurrence.
    std::vector<std::int32_t> sample_columns;
    std::vector<std::int32_t> sample_rows;
    std::vector<double> sample_x_errors;
    std::vector<double> sample_y_errors;

    bool matches(
        double requested_x_start,
        double requested_x_step,
        int requested_column_count,
        double requested_y_start,
        double requested_y_step,
        int requested_row_count,
        const double* requested_velocity_x,
        const double* requested_velocity_y,
        int requested_action_count,
        int requested_frames_per_layer,
        bool requested_clamp
    ) const {
        if (
            x_start != requested_x_start
            || x_step != requested_x_step
            || column_count != requested_column_count
            || y_start != requested_y_start
            || y_step != requested_y_step
            || row_count != requested_row_count
            || frames_per_layer != requested_frames_per_layer
            || clamp_to_bounds != requested_clamp
            || static_cast<int>(velocity_x.size())
                != requested_action_count
        ) {
            return false;
        }
        for (int index = 0; index < requested_action_count; ++index) {
            if (
                velocity_x[index] != requested_velocity_x[index]
                || velocity_y[index] != requested_velocity_y[index]
            ) {
                return false;
            }
        }
        return true;
    }
};

inline Sample sample_lattice(
    double x,
    double y,
    double x_start,
    double x_step,
    int column_count,
    double y_start,
    double y_step,
    int row_count,
    bool clamp_to_bounds
) {
    const double x_end = x_start + x_step * (column_count - 1);
    const double y_end = y_start + y_step * (row_count - 1);
    bool inside = (
        x >= x_start && x <= x_end && y >= y_start && y <= y_end
    );
    if (clamp_to_bounds) {
        x = std::min(x_end, std::max(x_start, x));
        y = std::min(y_end, std::max(y_start, y));
        inside = true;
    }
    int column = static_cast<int>(std::nearbyint((x - x_start) / x_step));
    int row = static_cast<int>(std::nearbyint((y - y_start) / y_step));
    column = std::min(column_count - 1, std::max(0, column));
    row = std::min(row_count - 1, std::max(0, row));
    const double center_x = x_start + column * x_step;
    const double center_y = y_start + row * y_step;
    return {
        row,
        column,
        std::hypot(x - center_x, y - center_y),
        inside,
    };
}

inline std::size_t transition_axis_index(
    int active,
    int selected,
    int delay,
    int coordinate,
    int step,
    int action_count,
    int delay_slot_count,
    int coordinate_count,
    int frames_per_layer
) {
    return (
        (
            (
                (
                    static_cast<std::size_t>(active) * action_count
                    + static_cast<std::size_t>(selected)
                )
                * delay_slot_count
                + static_cast<std::size_t>(delay)
            )
            * coordinate_count
            + static_cast<std::size_t>(coordinate)
        )
        * frames_per_layer
        + static_cast<std::size_t>(step)
    );
}

inline Sample transition_sample(
    const TransitionTable& table,
    int active,
    int selected,
    int delay,
    int row,
    int column,
    int step,
    int action_count
) {
    const int delay_slot_count = table.frames_per_layer + 1;
    const std::size_t x_index = transition_axis_index(
        active,
        selected,
        delay,
        column,
        step,
        action_count,
        delay_slot_count,
        table.column_count,
        table.frames_per_layer
    );
    const std::size_t y_index = transition_axis_index(
        active,
        selected,
        delay,
        row,
        step,
        action_count,
        delay_slot_count,
        table.row_count,
        table.frames_per_layer
    );
    const std::int32_t sample_column = table.sample_columns[x_index];
    const std::int32_t sample_row = table.sample_rows[y_index];
    return {
        sample_row,
        sample_column,
        std::hypot(
            table.sample_x_errors[x_index],
            table.sample_y_errors[y_index]
        ),
        sample_column >= 0 && sample_row >= 0,
    };
}

inline std::shared_ptr<const TransitionTable> transition_table(
    double x_start,
    double x_step,
    int column_count,
    double y_start,
    double y_step,
    int row_count,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    int frames_per_layer,
    bool clamp_to_bounds
) {
    static std::mutex cache_mutex;
    static std::shared_ptr<const TransitionTable> cached;
    std::lock_guard<std::mutex> lock(cache_mutex);
    if (
        cached
        && cached->matches(
            x_start,
            x_step,
            column_count,
            y_start,
            y_step,
            row_count,
            velocity_x,
            velocity_y,
            action_count,
            frames_per_layer,
            clamp_to_bounds
        )
    ) {
        return cached;
    }

    auto table = std::make_shared<TransitionTable>();
    table->x_start = x_start;
    table->x_step = x_step;
    table->column_count = column_count;
    table->y_start = y_start;
    table->y_step = y_step;
    table->row_count = row_count;
    table->velocity_x.assign(velocity_x, velocity_x + action_count);
    table->velocity_y.assign(velocity_y, velocity_y + action_count);
    table->frames_per_layer = frames_per_layer;
    table->clamp_to_bounds = clamp_to_bounds;

    const int delay_slot_count = frames_per_layer + 1;
    const std::size_t x_sample_count = (
        static_cast<std::size_t>(action_count)
        * action_count
        * delay_slot_count
        * column_count
        * frames_per_layer
    );
    const std::size_t y_sample_count = (
        static_cast<std::size_t>(action_count)
        * action_count
        * delay_slot_count
        * row_count
        * frames_per_layer
    );
    table->sample_columns.resize(x_sample_count);
    table->sample_rows.resize(y_sample_count);
    table->sample_x_errors.resize(x_sample_count);
    table->sample_y_errors.resize(y_sample_count);
    for (int active = 0; active < action_count; ++active) {
        for (int selected = 0; selected < action_count; ++selected) {
            for (int delay = 0; delay <= frames_per_layer; ++delay) {
                for (int column = 0; column < column_count; ++column) {
                    const double start_x = x_start + column * x_step;
                    for (
                        int step = 1;
                        step <= frames_per_layer;
                        ++step
                    ) {
                        const int active_frames = std::min(step, delay);
                        const int selected_frames = std::max(step - delay, 0);
                        const Sample sample = sample_lattice(
                            start_x
                                + velocity_x[active] * active_frames
                                + velocity_x[selected] * selected_frames,
                            y_start,
                            x_start,
                            x_step,
                            column_count,
                            y_start,
                            y_step,
                            row_count,
                            clamp_to_bounds
                        );
                        const std::size_t output_index = transition_axis_index(
                            active,
                            selected,
                            delay,
                            column,
                            step - 1,
                            action_count,
                            delay_slot_count,
                            column_count,
                            frames_per_layer
                        );
                        table->sample_columns[output_index] = (
                            sample.inside ? sample.column : -1
                        );
                        table->sample_x_errors[output_index] = sample.error;
                    }
                }
                for (int row = 0; row < row_count; ++row) {
                    const double start_y = y_start + row * y_step;
                    for (
                        int step = 1;
                        step <= frames_per_layer;
                        ++step
                    ) {
                        const int active_frames = std::min(step, delay);
                        const int selected_frames = std::max(step - delay, 0);
                        const Sample sample = sample_lattice(
                            x_start,
                            start_y
                                + velocity_y[active] * active_frames
                                + velocity_y[selected] * selected_frames,
                            x_start,
                            x_step,
                            column_count,
                            y_start,
                            y_step,
                            row_count,
                            clamp_to_bounds
                        );
                        const std::size_t output_index = transition_axis_index(
                            active,
                            selected,
                            delay,
                            row,
                            step - 1,
                            action_count,
                            delay_slot_count,
                            row_count,
                            frames_per_layer
                        );
                        table->sample_rows[output_index] = (
                            sample.inside ? sample.row : -1
                        );
                        table->sample_y_errors[output_index] = sample.error;
                    }
                }
            }
        }
    }
    cached = table;
    return cached;
}
