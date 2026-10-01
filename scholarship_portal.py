"""CCCS 106 Week 5: CSPC Scholarship Intake Portal starter scaffold.

Target: Python 3.12+ and Flet 0.86.5.
Complete the Tier 2 validators and Tier 1 submission TODOs in later phases.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime

import flet as ft


# TIER 3: DOMAIN DATA CONTRACT & CUSTOM EXCEPTIONS


class ScholarshipValidationError(Exception):
    """Base exception for scholarship domain validation failures."""


class IDFormatError(ScholarshipValidationError):
    """Student ID does not conform to the CSPC format."""


class EmailDomainError(ScholarshipValidationError):
    """Email does not belong to the institutional CSPC domain."""


class GWARangeError(ScholarshipValidationError):
    """GWA is non-numeric or outside the 1.00 to 5.00 grading scale."""


@dataclass(frozen=True)
class ScholarshipApplicant:
    """Immutable applicant record to be created after all validation passes."""

    full_name: str
    student_id: str
    email: str
    phone: str
    gwa: float
    program: str
    submitted_at: datetime = field(default_factory=datetime.now)


# TIER 2: VALIDATION ENGINE


class ScholarshipValidator:
    """Scholarship input rules; unfinished validators explicitly raise errors."""

    NAME_REGEX = re.compile(r"^[A-Za-z\s.\-',]{2,60}$")
    STUDENT_ID_REGEX = re.compile(r"^20\d{2}-\d{4,5}$")
    CSPC_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@cspc\.edu\.ph$")
    PH_PHONE_REGEX = re.compile(r"^(?:\+63|0)9\d{9}$")

    @classmethod
    def sanitize_string(cls, raw: str | None) -> str:
        """Trim surrounding whitespace and treat None as an empty string."""
        return (raw or "").strip()

    @classmethod
    def validate_name(cls, value: str | None) -> str:
        """Return a trimmed name or raise ScholarshipValidationError."""
        clean = cls.sanitize_string(value)
        if not clean:
            raise ScholarshipValidationError("Full name is required.")
        if not cls.NAME_REGEX.fullmatch(clean):
            raise ScholarshipValidationError(
                "Enter a valid name (2–60 letters, hyphens, or periods)."
            )
        return clean

    @classmethod
    def validate_student_id(cls, value: str | None) -> str:
        """TODO: Return a trimmed CSPC ID or raise IDFormatError."""
        # TODO: Sanitize, check required input, and match STUDENT_ID_REGEX.
        raise NotImplementedError("Student ID validation is not implemented yet.")

    @classmethod
    def validate_email(cls, value: str | None) -> str:
        """TODO: Return a lowercase CSPC email or raise EmailDomainError."""
        # TODO: Sanitize, lowercase, check required input, and match CSPC_EMAIL_REGEX.
        raise NotImplementedError("Email validation is not implemented yet.")

    @classmethod
    def validate_phone(cls, value: str | None) -> str:
        """TODO: Return a local PH mobile number or raise ScholarshipValidationError."""
        # TODO: Remove spaces/hyphens, match PH_PHONE_REGEX, and normalize +63 to 0.
        raise NotImplementedError("Phone validation is not implemented yet.")

    @classmethod
    def validate_gwa(cls, value: str | None) -> float:
        """TODO: Return a rounded, finite GWA in 1.00–5.00 or raise GWARangeError."""
        # TODO: Parse defensively, reject non-finite/out-of-range values, and round.
        raise NotImplementedError("GWA validation is not implemented yet.")


# TIER 1: FLET PRESENTATION LAYER


def main(page: ft.Page) -> None:
    """Build the runnable form without accepting unfinished applications."""
    page.title = "CSPC Scholarship Intake Portal"
    page.window.width = 620
    page.window.height = 780
    page.window.resizable = False
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 25

    # TODO: Append verified records here after completing the submission pipeline.
    approved_applicants: list[ScholarshipApplicant] = []

    name_field = ft.TextField(
        label="Full Name",
        hint_text="e.g., Maria Clara Santos",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border_radius=8,
    )
    id_field = ft.TextField(
        label="Student ID Number",
        hint_text="e.g., 2024-0123",
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        border_radius=8,
    )
    email_field = ft.TextField(
        label="Institutional Email",
        hint_text="e.g., mclara.santos@cspc.edu.ph",
        prefix_icon=ft.Icons.ALTERNATE_EMAIL,
        border_radius=8,
    )
    phone_field = ft.TextField(
        label="Philippine Mobile Number",
        hint_text="e.g., 09181234567 or +639181234567",
        prefix_icon=ft.Icons.PHONE_ANDROID_OUTLINED,
        border_radius=8,
    )
    gwa_field = ft.TextField(
        label="Academic General Weighted Average (GWA)",
        hint_text="Scale: 1.00 (highest) to 5.00 (failing)",
        prefix_icon=ft.Icons.GRADE_OUTLINED,
        border_radius=8,
    )
    program_dropdown = ft.Dropdown(
        label="Scholarship Program",
        hint_text="Select your scholarship grant",
        leading_icon=ft.Icons.SCHOOL_OUTLINED,
        border_radius=8,
        options=[
            ft.DropdownOption("CHED Tulong Dunong Program (TDP)"),
            ft.DropdownOption("DOST Science & Technology Scholarship"),
            ft.DropdownOption("CSPC Institutional Academic Scholarship"),
            ft.DropdownOption("UniFAST Tertiary Education Subsidy (TES)"),
        ],
    )
    status_summary = ft.Text(
        value="Starter scaffold: validation and submission pending.",
        color=ft.Colors.GREY_400,
        size=13,
    )

    def clear_field_error(event: ft.Event[ft.TextField]) -> None:
        """Clear a text field's previous error when the user types."""
        if event.control.error is not None:
            event.control.error = None
            page.update()

    def clear_dropdown_error(event: ft.Event[ft.Dropdown]) -> None:
        """Clear the dropdown's previous error when a selection changes."""
        if event.control.error_text is not None:
            event.control.error_text = None
            page.update()

    text_fields = (name_field, id_field, email_field, phone_field, gwa_field)
    for text_field in text_fields:
        text_field.on_change = clear_field_error
    program_dropdown.on_select = clear_dropdown_error

    def submit_application(event: ft.Event[ft.FilledButton]) -> None:
        """Run starter checks and stop before the unfinished validation pipeline."""
        has_errors = False
        for text_field in text_fields:
            text_field.error = None
        program_dropdown.error_text = None

        try:
            clean_name = ScholarshipValidator.validate_name(name_field.value)
        except ScholarshipValidationError as err:
            name_field.error = str(err)
            has_errors = True

        # TODO: Validate ID, email, phone, and GWA in independent try/except blocks.
        # Set each control's error and has_errors using the domain exception text.

        if not program_dropdown.value:
            program_dropdown.error_text = (
                "Please select an accredited scholarship program."
            )
            has_errors = True

        if has_errors:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(
                        "Validation failed: Please correct highlighted fields."
                    ),
                    bgcolor=ft.Colors.RED_700,
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
            )
            page.update()
            return

        # TODO: Check program membership against the predefined dropdown options.
        # TODO: Replace this starter stop after ALL validation checks are implemented.
        # Create ScholarshipApplicant from clean values, append to approved_applicants,
        # render a recent intake card, show success, reset inputs, and update the count.
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(
                    "Starter scaffold only: validation and submission are not "
                    "implemented yet. No application was accepted."
                ),
                bgcolor=ft.Colors.BLUE_700,
                behavior=ft.SnackBarBehavior.FLOATING,
            )
        )
        page.update()

    submit_button = ft.FilledButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE),
                ft.Text(
                    "Submit Scholarship Application", weight=ft.FontWeight.BOLD
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_700,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        height=48,
        on_click=submit_application,
    )

    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.LOCAL_POLICE,
                            size=32,
                            color=ft.Colors.BLUE_400,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "CSPC Scholarship Intake Portal",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Office of Student Affairs & Services • "
                                    "Academic Year 2026–2027",
                                    size=12,
                                    color=ft.Colors.GREY_400,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ]
                ),
                ft.Divider(height=20, color=ft.Colors.OUTLINE_VARIANT),
                name_field,
                id_field,
                email_field,
                phone_field,
                gwa_field,
                program_dropdown,
                ft.Container(height=10),
                submit_button,
                ft.Container(height=5),
                status_summary,
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
