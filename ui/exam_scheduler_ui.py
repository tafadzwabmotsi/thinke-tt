from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Collapsible, Label, Header, Input, Checkbox
from textual.containers import VerticalScroll, HorizontalScroll
from lib.exam_council import ExamCouncil
from lib.grade import EceswaGrade
from lib.subject import EceswaEgcseSubject as EgcseSubject, EceswaJcSubject as JcSubject
from lib.typing.data.schedule import DayOfWeek, PrioritizedCouncil, ScheduleInputData
from datetime import datetime
from textual.reactive import reactive
from lib.utils import LibUtils


class ExamSchedulerUI(App):
    """
    A Textual TUI application that collects exam preparation scheduling data 
    including:
    - Start and end dates
    - Days to exclude
    - Prioritized exam councils per subject

    The app builds a `ScheduleInputData` object upon form submission and exits
    with it for later use in schedule generation.
    """

    CSS_PATH = "styles.tcss"

    # Reactive fields bound to form state
    start_date = reactive(LibUtils.get_todays_date())
    end_date = reactive(LibUtils.get_next_months_date())
    excluded_days = reactive(list) 
    prioritized_councils = reactive(list)

    # Final output
    schedule_input_data: Optional[ScheduleInputData] = None

    def __init__(self, grade: EceswaGrade):
        """
        Initialize the TUI form based on the selected grade level.

        Args:
            grade (EceswaGrade): The educational grade level (JC or EGCSE).
        """
        super().__init__()
        self.grade = grade.value

        # Collect subjects for the given grade
        self.grade_subjects = [
            subject.value for subject in (
                EgcseSubject if grade == EceswaGrade.EGCSE else JcSubject
            )
        ]

        # Validation flags
        self.start_date_valid = False
        self.end_date_valid = False
        self.prioritized_councils_valid = False
        self.is_form_valid = False

    def compose(self) -> ComposeResult:
        """
        Compose the user interface with labeled input fields and collapsible components.
        """
        start_date_label = LibUtils.get_human_readable_date(self.start_date)
        end_date_label = LibUtils.get_human_readable_date(self.end_date)

        yield VerticalScroll(
            Header(),

            # Start date input
            Label("Enter start date:"),
            Input(placeholder=start_date_label, id="start_date_input", classes="input"),
    
            # End date input
            Label("Enter end date:"),
            Input(placeholder=end_date_label, id="end_date_input", classes="input"),

            # Excluded days checkboxes
            Label("Choose day(s) to exclude from the schedule:"),
            HorizontalScroll(
                *[
                    Checkbox(day.value, id=f"day_checkbox_{i}", classes="checkbox")
                    for i, day in enumerate(DayOfWeek)
                ],
                classes="input valid",
                id="excluded_days_scroll",
            ),

            # Prioritized councils section
            Label("Select subject prioritized exam councils (Optional):"),
            Collapsible(
                VerticalScroll(
                    *self._get_prioritized_council_collapsibles(),
                    id="prioritized_councils_scroll",
                ),
                id="prioritized_councils_collapsible",
                classes="input",
                title="Prioritized exam councils"
            ),

            # Submission button
            Button("Save", id="insert_button", disabled=not self.is_form_valid),

            Footer(),
            id="exam_schedule_container"
        )

    def _validate_fields(self):
        """
        Checks overall form validity and updates button state and styling accordingly.
        """
        self.is_form_valid = (
            self.start_date_valid and 
            self.end_date_valid and 
            self.prioritized_councils_valid
        )

        button = self.query_one("#insert_button", Button)
        button.remove_class("enable-button", "disable-button")
        button.add_class("enable-button" if self.is_form_valid else "disable-button")
        button.disabled = not self.is_form_valid

    def _validate_prioritized_councils(self) -> None:
        """
        Validates each subject's council selection to ensure at least one checkbox
        is checked. Adds CSS classes to reflect validity. Also updates the
        `prioritized_councils` reactive variable.
        """
        vertical_scroll_valid = True
        vertical_scroll = self.query_one("#prioritized_councils_scroll", VerticalScroll)

        for collapsible in vertical_scroll.query(Collapsible):
            if collapsible.id == "prioritized_councils_collapsible":
                continue
            
            horizontal_scroll = collapsible.query_one(HorizontalScroll)
            checkboxes = horizontal_scroll.query(Checkbox)
            horizontal_valid = any(checkbox.value for checkbox in checkboxes)

            # Style update
            horizontal_scroll.remove_class("valid", "invalid")
            horizontal_scroll.add_class("valid" if horizontal_valid else "invalid")

            collapsible.remove_class("valid", "invalid")
            collapsible.add_class("valid" if horizontal_valid else "invalid")

            vertical_scroll_valid = vertical_scroll_valid and horizontal_valid

        # Style outer scroll and collapsible
        vertical_scroll.remove_class("valid", "invalid")
        vertical_scroll.add_class("valid" if vertical_scroll_valid else "invalid")

        outer_collapsible = self.query_one("#prioritized_councils_collapsible", Collapsible)
        outer_collapsible.remove_class("valid", "invalid")
        outer_collapsible.add_class("valid" if vertical_scroll_valid else "invalid")

        # Update form validation state
        self.prioritized_councils_valid = vertical_scroll_valid

    def _get_prioritized_council_collapsibles(self) -> list[Collapsible]:
        """
        Dynamically generate collapsible UI components for each subject with 
        council checkboxes. Some subjects only allow ECESWA by default.
        """
        collapsibles = []

        for i, subject in enumerate(self.grade_subjects):
            subject_id = "_".join(subject.lower().split(" "))
            is_jc_exclusive = (
                self.grade == EceswaGrade.JC.value and subject in [
                    JcSubject.SISWATI.value, 
                    JcSubject.RELIGIOUS_EDUCATION.value,
                    JcSubject.FRENCH.value,
                    JcSubject.HISTORY.value,
                    JcSubject.CONSUMER_SCIENCE.value
                ]
            )
            
            is_egcse_siswati = (
                self.grade == EceswaGrade.EGCSE.value and subject in [
                    EgcseSubject.FIRST_SISWATI.value,
                    EgcseSubject.SECOND_SISWATI.value,
                    EgcseSubject.HISTORY.value,
                    EgcseSubject.RELIGIOUS_EDUCATION.value,
                ]
            )

            checkboxes = (
                [Checkbox(ExamCouncil.ECESWA.value, value=True, id=f"{subject_id}_checkbox", classes="checkbox")]
                if is_jc_exclusive or is_egcse_siswati else [
                    Checkbox(council.value, value=True, id=f"{subject_id}_checkbox_{j}", classes="checkbox")
                    for j, council in enumerate(ExamCouncil)
                ]
            )

            collapsibles.append(
                Collapsible(
                    HorizontalScroll(
                        *checkboxes,
                        classes="input",
                        id=f"{subject_id}_prioritized_councils_scroll",
                    ),
                    classes="input",
                    title=subject,
                    collapsed=False,
                    id=f"{subject_id}_prioritized_councils_collapsible",
                )
            )

        return collapsibles

    def _collect_prioritized_councils(self) -> list[PrioritizedCouncil]:
        """
        Traverse the UI to gather user-selected prioritized councils per subject
        into structured `PrioritizedCouncil` dataclasses.
        """
        vertical_scroll = self.query_one("#prioritized_councils_scroll", VerticalScroll)
        result: list[PrioritizedCouncil] = []

        for collapsible in vertical_scroll.query(Collapsible):
            if collapsible.id == "prioritized_councils_collapsible":
                continue

            subject = collapsible.title
            horizontal_scroll = collapsible.query_one(HorizontalScroll)
            checkboxes = horizontal_scroll.query(Checkbox)

            selected_councils = [
                str(checkbox.label) for checkbox in checkboxes if checkbox.value
            ]

            if selected_councils:
                result.append(PrioritizedCouncil(subject=subject, councils=selected_councils))

        return result

    def on_input_changed(self, event: Input.Changed):
        """
        Handles input validation for date fields, applying valid/invalid CSS
        styling and updating the form state.
        """
        def is_valid_date(input_str: str) -> bool:
            try:
                datetime.strptime(input_str, "%d %B %Y")
                return True
            except ValueError:
                return False

        if event.input.id == "start_date_input":
            value = event.value.strip()
            valid = is_valid_date(value)
            event.input.remove_class("valid", "invalid")
            event.input.add_class("valid" if valid else "invalid")
            self.start_date_valid = valid
            self.start_date = value

        if event.input.id == "end_date_input":
            value = event.value.strip()
            valid = is_valid_date(value)
            event.input.remove_class("valid", "invalid")
            event.input.add_class("valid" if valid else "invalid")
            self.end_date_valid = valid
            self.end_date = value

        self._validate_fields()

    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """
        Handles checkbox changes for:
        - Updating excluded days
        - Validating prioritized councils
        """
        excluded_days_container = self.query_one("#excluded_days_scroll", HorizontalScroll)
        checkboxes = excluded_days_container.query(Checkbox)

        # Collect unique selected day labels
        self.excluded_days = list({
            str(checkbox.label)
            for checkbox in checkboxes
            if checkbox.value
        })

        self._validate_prioritized_councils()
        self._validate_fields()

    def on_mount(self) -> None:
        """
        Called when the app is ready to be displayed. Performs initial validation.
        """
        self._validate_fields()
        self._validate_prioritized_councils()
        self.title = f"Insert Exam Preparation Schedule Input - {self.grade} Students"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handles the form submission. If the form is valid, collects all the data
        into a `ScheduleInputData` object and exits the application with it.
        """
        if event.button.id == "insert_button" and self.is_form_valid:
            self.schedule_input_data = ScheduleInputData(
                start_date=LibUtils.get_machine_readable_date(self.start_date),
                end_date=LibUtils.get_machine_readable_date(self.end_date),
                excluded_days=self.excluded_days,
                prioritized_councils=self._collect_prioritized_councils()
            )
            self.exit(self.schedule_input_data)
