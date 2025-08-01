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
    A Textual TUI application that collects exam 
    preparation scheduling data.
    """

    CSS_PATH = "styles.tcss"
    
    start_date = reactive(LibUtils.get_todays_date())
    end_date = reactive(LibUtils.get_next_months_date())
    excluded_days = reactive(list)
    prioritized_councils = reactive(list)
    
    schedule_input_data: Optional[ScheduleInputData] = None
    
    
    def __init__(self, grade: EceswaGrade):
        super().__init__()
        self.grade = grade.value
        
        self.grade_subjects = [
            subject.value for subject in (
                EgcseSubject if grade == EceswaGrade.EGCSE else JcSubject
            )
        ]
        

        # Validation variables
        self.start_date_valid = False
        self.end_date_valid = False
        self.prioritized_councils_valid = False
        self.is_form_valid = False
    
    def compose(self) -> ComposeResult:
        start_date_label = LibUtils.get_human_readable_date(self.start_date)
        end_date_label = LibUtils.get_human_readable_date(self.end_date)
        
        yield VerticalScroll(
            Header(),
            # Start date field
            Label(f"Enter start date:"),
            Input(placeholder=start_date_label, id="start_date_input", classes="input"),

            # End date field
            Label(f"Enter end date:"),
            Input(placeholder=end_date_label, id="end_date_input", classes="input"),
            
            # Excluded days field
            Label("Choose day(s) to exclude from the schedule:"),
            HorizontalScroll(
                *[
                    Checkbox(day.value, id=f"day_checkbox_{i}", classes="checkbox")
                    for i, day in enumerate(DayOfWeek)
                ],
                classes="input valid",
                id="excluded_days_scroll",
            ),
            
            # Prioritized exam councils field
            Label("Select subject prioritized exam councils(Optional):"),
            Collapsible(
                VerticalScroll(
                    *self._get_prioritized_council_collapsibles(),
                    id="prioritized_councils_scroll",
                ),
                id="prioritized_councils_collapsible",
                classes="input",
                title="Prioritized exam councils"  
            ),
            Button("Save", id="insert_button", disabled=not self.is_form_valid),
            Footer(),
            id="exam_schedule_container"
        ) 
    
    def _validate_fields(self):
        self.is_form_valid = self.start_date_valid and self.end_date_valid and self.prioritized_councils_valid
        button = self.query_one("#insert_button", Button)
        
        button.remove_class("enable-button", "disable-button")
        button.add_class("enable-button" if self.is_form_valid else "disable-button")
        button.disabled = not self.is_form_valid

    def _validate_prioritized_councils(self) -> None:
        """Validates the nested prioritized councils form and sets CSS classes accordingly."""

        vertical_scroll_valid = True

        vertical_scroll = self.query_one("#prioritized_councils_scroll", VerticalScroll)

        for collapsible in vertical_scroll.query(Collapsible):
            # Skip the outer collapsible if somehow included
            if collapsible.id == "prioritized_councils_collapsible":
                continue

            horizontal_scroll = collapsible.query_one(HorizontalScroll)
            checkboxes = horizontal_scroll.query(Checkbox)
            horizontal_valid = any(checkbox.value for checkbox in checkboxes)

            horizontal_scroll.remove_class("valid", "invalid")
            horizontal_scroll.add_class("valid" if horizontal_valid else "invalid")

            collapsible.remove_class("valid", "invalid")
            collapsible.add_class("valid" if horizontal_valid else "invalid")

            vertical_scroll_valid = vertical_scroll_valid and horizontal_valid

        vertical_scroll.remove_class("valid", "invalid")
        vertical_scroll.add_class("valid" if vertical_scroll_valid else "invalid")

        outer_collapsible = self.query_one("#prioritized_councils_collapsible", Collapsible)
        outer_collapsible.remove_class("valid", "invalid")
        outer_collapsible.add_class("valid" if vertical_scroll_valid else "invalid")

        self.prioritized_councils_valid = vertical_scroll_valid
    
    def _get_prioritized_council_collapsibles(self) -> list[Collapsible]:
        collapsibles = []

        for i, subject in enumerate(self.grade_subjects):
            subject_id = "_".join(subject.lower().split(" "))
            is_jc_exclusive = (
                self.grade == EceswaGrade.JC.value and subject in [
                    JcSubject.SISWATI.value, 
                    JcSubject.RELIGIOUS_EDUCATION.value,
                    JcSubject.FRENCH.value,
                    JcSubject.HISTORY.value
                ]
            )

            checkboxes = (
                [
                    Checkbox(
                        ExamCouncil.ECESWA.value,
                        value=True,
                        id=f"{subject_id}_eceswa_only_checkbox",
                        classes="checkbox",
                    )
                ]
                if is_jc_exclusive
                else [
                    Checkbox(
                        council.value,
                        value=True,
                        id=f"{subject_id}_checkbox_{j}",
                        classes="checkbox",
                    )
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
        def is_valid_date(input_str: str) -> bool:
            try:
                datetime.strptime(input_str, "%d %B %Y")
                return True
            except ValueError:
                return False
            
        if event.input.id == "start_date_input":
            value = event.value.strip()
            
            date_valid = is_valid_date(value)
            event.input.remove_class("valid", "invalid")
            event.input.add_class("valid" if date_valid else "invalid")
            self.start_date_valid = date_valid
            self.start_date = value
            
        if event.input.id == "end_date_input":
            value = event.value.strip()
            
            date_valid = is_valid_date(value)
            event.input.remove_class("valid", "invalid")
            event.input.add_class("valid" if date_valid else "invalid")
            self.end_date_valid = date_valid
            self.end_date = value
            
        self._validate_fields()
        
    
    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        # Handle excluded days update
        excluded_days_container = self.query_one("#excluded_days_scroll", HorizontalScroll)
        checkboxes = excluded_days_container.query(Checkbox)
        
        self.excluded_days = list({
            str(checkbox.label)
            for checkbox in checkboxes
            if checkbox.value
        })

        self._validate_prioritized_councils()
        self._validate_fields()
        
    def on_mount(self) -> None:
        self._validate_fields()
        self._validate_prioritized_councils()
        self.title = f"Insert Exam Preparation Schedule Input - {self.grade} Students"
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "insert_button" and self.is_form_valid:
            self.schedule_input_data = ScheduleInputData(
                start_date=self.start_date,
                end_date=self.end_date,
                excluded_days=self.excluded_days,
                prioritized_councils=self._collect_prioritized_councils()
            ) 
            self.exit(self.schedule_input_data)
             
