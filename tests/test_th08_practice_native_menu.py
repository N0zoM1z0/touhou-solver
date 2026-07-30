from __future__ import annotations

import unittest
from unittest.mock import patch

from th08_automation import practice_native_menu


class PracticeNativeMenuTests(unittest.TestCase):
    def test_title_wait_tolerates_transient_unallocated_manager(self) -> None:
        interactive = {
            "mode": practice_native_menu.TITLE_MODE_MAIN,
            "substate": 1,
        }
        with patch.object(
            practice_native_menu,
            "read_title_menu_state",
            side_effect=(
                RuntimeError("title menu manager is not allocated"),
                interactive,
            ),
        ):
            state = practice_native_menu.wait_for_title_menu(
                object(),
                123,
                mode=practice_native_menu.TITLE_MODE_MAIN,
                timeout_seconds=1.0,
            )

        self.assertEqual(state, interactive)


if __name__ == "__main__":
    unittest.main()
