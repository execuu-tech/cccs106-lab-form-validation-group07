"""Supplementary domain and UI acceptance tests for the completed portal."""

from dataclasses import FrozenInstanceError
from datetime import datetime
import unittest
from unittest.mock import MagicMock, patch

import flet as ft
import scholarship_portal as portal


def text_values(control: ft.Control) -> list[str]:
    """Collect visible text from a nested card or section."""
    if isinstance(control, ft.Text):
        return [control.value]
    values = []
    for child in getattr(control, "controls", None) or []:
        values.extend(text_values(child))
    content = getattr(control, "content", None)
    if isinstance(content, ft.Control):
        values.extend(text_values(content))
    return values


class TestPortalAcceptance(unittest.TestCase):
    """Verify domain edge cases and actual submission outcomes headlessly."""

    def setUp(self) -> None:
        self.page = MagicMock(spec=ft.Page)
        self.page.window = MagicMock()
        portal.main(self.page)
        self.column = self.page.add.call_args.args[0]
        self.fields = self.column.controls[2:7]
        self.dropdown = self.column.controls[7]
        self.button = next(
            c for c in self.column.controls if isinstance(c, ft.FilledButton)
        )
        self.summary = self.column.controls[11]
        self.recent_section = self.column.controls[12]
        self.cards = self.recent_section.controls[1]

    def populate_valid(self, name: str = "Maria Clara Santos") -> None:
        """Set one valid application without dispatching change events."""
        values = [
            name, "2024-0891", "mclara.santos@cspc.edu.ph",
            "09181234567", "1.45",
        ]
        for control, value in zip(self.fields, values):
            control.value = value
        self.dropdown.value = "DOST Science & Technology Scholarship"

    def submit(self) -> None:
        """Dispatch the real submission handler with a Flet click event."""
        self.button.on_click(ft.Event("click", self.button))

    def test_none_inputs_raise_exact_domain_exceptions(self) -> None:
        cases = [
            (portal.ScholarshipValidator.validate_name,
             portal.ScholarshipValidationError),
            (portal.ScholarshipValidator.validate_student_id,
             portal.IDFormatError),
            (portal.ScholarshipValidator.validate_email,
             portal.EmailDomainError),
            (portal.ScholarshipValidator.validate_phone,
             portal.ScholarshipValidationError),
            (portal.ScholarshipValidator.validate_gwa,
             portal.GWARangeError),
        ]
        for method, expected in cases:
            with self.subTest(method=method.__name__):
                with self.assertRaises(expected) as raised:
                    method(None)
                self.assertIs(type(raised.exception), expected)

    def test_nonfinite_and_pre_rounding_gwa_rejection(self) -> None:
        cases = {
            "nan": "GWA must be a valid number between 1.00 and 5.00.",
            "inf": "GWA must be a valid number between 1.00 and 5.00.",
            "-inf": "GWA must be a valid number between 1.00 and 5.00.",
            "1e309": "GWA must be a valid number between 1.00 and 5.00.",
            "0.999": "GWA must be between 1.00 and 5.00.",
            "5.001": "GWA must be between 1.00 and 5.00.",
        }
        for value, message in cases.items():
            with self.subTest(value=value):
                with self.assertRaises(portal.GWARangeError) as raised:
                    portal.ScholarshipValidator.validate_gwa(value)
                self.assertEqual(str(raised.exception), message)

    def test_gwa_rounding(self) -> None:
        self.assertEqual(portal.ScholarshipValidator.validate_gwa(" 1.456 "),
                         1.46)

    def test_name_length_boundaries(self) -> None:
        validate = portal.ScholarshipValidator.validate_name
        self.assertEqual(validate("Al"), "Al")
        self.assertEqual(validate("A" * 60), "A" * 60)
        with self.assertRaises(portal.ScholarshipValidationError):
            validate("A" * 61)

    def test_all_invalid_fields_show_errors_without_a_record(self) -> None:
        values = ["Juan123", "24-0123", "juan@gmail.com", "08123456789", "uno"]
        for control, value in zip(self.fields, values):
            control.value = value
        with patch.object(portal, "ScholarshipApplicant",
                          wraps=portal.ScholarshipApplicant) as create:
            self.submit()
        create.assert_not_called()
        expected = [
            "Enter a valid name (2\u201360 letters, hyphens, or periods).",
            "Invalid Student ID. Expected format: YYYY-NNNN (e.g., 2024-0123).",
            "Institutional email required (must end with @cspc.edu.ph).",
            "Invalid mobile number. Expected: 09XXXXXXXXX or +639XXXXXXXXX.",
            "GWA must be a valid number between 1.00 and 5.00.",
        ]
        self.assertEqual([c.error for c in self.fields], expected)
        self.assertEqual(self.dropdown.error_text,
                         "Please select an accredited scholarship program.")
        self.assertEqual([c.value for c in self.fields], values)
        self.assertEqual(self.cards.controls, [])
        self.assertFalse(self.recent_section.visible)
        self.assertEqual(self.summary.value, "Ready to accept applications.")
        bar = self.page.show_dialog.call_args.args[0]
        self.assertEqual(bar.bgcolor, ft.Colors.RED_700)
        self.assertEqual(bar.behavior, ft.SnackBarBehavior.FLOATING)
        self.assertEqual(bar.content.value,
                         "Validation failed: Please correct highlighted fields.")

    def test_unknown_program_is_rejected(self) -> None:
        self.populate_valid()
        self.dropdown.value = "Unsupported Scholarship"
        with patch.object(portal, "ScholarshipApplicant",
                          wraps=portal.ScholarshipApplicant) as create:
            self.submit()
        create.assert_not_called()
        self.assertTrue(all(c.error is None for c in self.fields))
        self.assertEqual(self.dropdown.error_text,
                         "Please select an accredited scholarship program.")
        self.assertEqual(self.cards.controls, [])

    def test_all_text_errors_clear_on_change(self) -> None:
        for control in self.fields:
            with self.subTest(label=control.label):
                control.error = "Previous error"
                self.page.update.reset_mock()
                control.on_change(ft.Event("change", control))
                self.assertIsNone(control.error)
                self.page.update.assert_called_once()
                self.page.update.reset_mock()
                control.on_change(ft.Event("change", control))
                self.page.update.assert_not_called()

    def test_dropdown_error_clears_on_select(self) -> None:
        self.dropdown.error_text = "Previous error"
        self.dropdown.value = "DOST Science & Technology Scholarship"
        self.page.update.reset_mock()
        self.dropdown.on_select(ft.Event("select", self.dropdown))
        self.assertIsNone(self.dropdown.error_text)
        self.page.update.assert_called_once()

    def test_cleared_error_does_not_bypass_validation(self) -> None:
        self.populate_valid()
        gwa = self.fields[4]
        gwa.value = "uno"
        self.submit()
        self.assertIsNotNone(gwa.error)
        gwa.on_change(ft.Event("change", gwa))
        self.assertIsNone(gwa.error)
        with patch.object(portal, "ScholarshipApplicant",
                          wraps=portal.ScholarshipApplicant) as create:
            self.submit()
        create.assert_not_called()
        self.assertIsNotNone(gwa.error)
        self.assertEqual(self.cards.controls, [])

    def test_success_normalizes_record_resets_and_renders(self) -> None:
        values = [
            " Maria Clara Santos ", " 2024-0891 ",
            " MCLARA.SANTOS@CSPC.EDU.PH ", "+63 918-123-4567", "1.456",
        ]
        for control, value in zip(self.fields, values):
            control.value = value
            control.error = "Old error"
        self.dropdown.value = "DOST Science & Technology Scholarship"
        self.dropdown.error_text = "Old error"
        with patch.object(portal, "ScholarshipApplicant",
                          wraps=portal.ScholarshipApplicant) as create:
            self.submit()
        create.assert_called_once_with(
            full_name="Maria Clara Santos", student_id="2024-0891",
            email="mclara.santos@cspc.edu.ph", phone="09181234567",
            gwa=1.46, program="DOST Science & Technology Scholarship",
        )
        self.assertTrue(all(c.error is None for c in self.fields))
        self.assertTrue(all(c.value == "" for c in self.fields))
        self.assertIsNone(self.dropdown.error_text)
        self.assertIsNone(self.dropdown.value)
        self.assertEqual(self.summary.value, "Total approved applicants: 1")
        self.assertTrue(self.recent_section.visible)
        self.assertEqual(len(self.cards.controls), 1)
        card_text = text_values(self.cards.controls[0])
        for expected in [
            "Maria Clara Santos", "Student ID: 2024-0891",
            "Email: mclara.santos@cspc.edu.ph", "Mobile: 09181234567",
            "GWA: 1.46", "Program: DOST Science & Technology Scholarship",
        ]:
            self.assertIn(expected, card_text)
        submitted = next(t for t in card_text if t.startswith("Submitted: "))
        datetime.strptime(submitted[11:], "%Y-%m-%d %H:%M:%S")
        bar = self.page.show_dialog.call_args.args[0]
        self.assertEqual(bar.bgcolor, ft.Colors.GREEN_700)
        self.assertEqual(bar.behavior, ft.SnackBarBehavior.FLOATING)
        self.assertEqual(bar.content.value,
                         "Application accepted for Maria Clara Santos!")

    def test_failure_preserves_session_and_cards_are_newest_first(self) -> None:
        self.populate_valid()
        self.submit()
        first_card = self.cards.controls[0]
        self.populate_valid("Juan Dela Cruz")
        self.fields[4].value = "0.80"
        self.submit()
        self.assertEqual(self.summary.value, "Total approved applicants: 1")
        self.assertEqual(self.cards.controls, [first_card])
        self.assertEqual(self.fields[0].value, "Juan Dela Cruz")
        self.fields[4].value = "1.25"
        self.submit()
        self.assertEqual(self.summary.value, "Total approved applicants: 2")
        self.assertEqual(len(self.cards.controls), 2)
        self.assertIn("Juan Dela Cruz", text_values(self.cards.controls[0]))
        self.assertIs(self.cards.controls[1], first_card)

    def test_new_page_starts_a_fresh_session(self) -> None:
        self.populate_valid()
        self.submit()
        new_page = MagicMock(spec=ft.Page)
        new_page.window = MagicMock()
        portal.main(new_page)
        col = new_page.add.call_args.args[0]
        self.assertEqual(col.controls[11].value, "Ready to accept applications.")
        self.assertFalse(col.controls[12].visible)
        self.assertEqual(col.controls[12].controls[1].controls, [])

    def test_record_is_frozen_and_timestamped(self) -> None:
        before = datetime.now()
        record = portal.ScholarshipApplicant(
            full_name="Maria Clara Santos", student_id="2024-0891",
            email="mclara.santos@cspc.edu.ph", phone="09181234567",
            gwa=1.45, program="DOST Science & Technology Scholarship",
        )
        self.assertIsInstance(record.submitted_at, datetime)
        self.assertGreaterEqual(record.submitted_at, before)
        self.assertLessEqual(record.submitted_at, datetime.now())
        with self.assertRaises(FrozenInstanceError):
            record.gwa = 1.00


if __name__ == "__main__":
    unittest.main()
