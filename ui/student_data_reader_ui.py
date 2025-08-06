import re
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, HorizontalScroll
from textual.widgets import Input, Label, RadioSet, RadioButton, Checkbox, Button, Footer
from textual.binding import Binding
from textual.reactive import reactive

from lib.grade import EceswaGrade
from lib.subject import EceswaEgcseSubject, EceswaJcSubject
from lib.typing.domain.student import StudentRecord

class StudentDataReaderUI(App):
    """
    A Textual TUI application for collecting and validating student data inputs.

    This form-based app allows users to enter a student's name, phone number,
    grade (JC or EGCSE), and select a set of subjects. Validation is performed 
    on input, and the resulting record is returned when the form is submitted.
    """

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding(key="q", action="quit", description="[Click to Close or Press Ctrl + C]"),
    ]

    NAME_REGEX = re.compile(r"^[A-Za-z]+(?: [A-Za-z]+)*$")
    PHONE_REGEX = re.compile(r"^\d{8}$")
    SUBJECTS_MIN_THRESHOLD = 5

    # Reactive state variables for input tracking and form validation
    student_name = reactive("")
    student_phone = reactive("")
    student_grade = reactive(EceswaGrade.EGCSE)
    student_subjects = reactive(list)

    # Validation variables
    student_name_valid = False
    student_phone_valid = False
    student_subjects_valid = False
    can_save_student_record = False

    subject_enum = EceswaEgcseSubject
    student_record: Optional[StudentRecord] = None

    def compose(self) -> ComposeResult:
        """
        Define the layout and components of the form UI.
        
        Returns:
            ComposeResult: A generator that yields all child widgets to render.
        """
        yield Container(
            VerticalScroll(
                Label("Student's Name:"),
                Input(placeholder="Enter name...", id="name_input", classes="input"),

                Label("Student's Phone(+268):"),
                Input(placeholder="7994...", id="phone_input", classes="input"),

                Label("Student Grade:"),
                RadioSet(
                    *(RadioButton(
                        grade.value, 
                        value=grade.name, 
                        classes="radio-button", 
                        id=f"radio_{i}"
                    ) for i, grade in enumerate(EceswaGrade)),
                    id="grade_radio",
                    classes="input"
                ),
    
                Label("Select Student's Subjects of Study:"),
                HorizontalScroll(
                    *self.render_subject_checkboxes(),
                    id="subject_list",
                    classes="input"
                ),
                Button("Save", id="save_button", disabled=self.can_save_student_record),
                Footer(),
                id="form"
            )
        )

    def render_subject_checkboxes(self) -> list[Checkbox]:
        """
        Render checkboxes for the available subjects from the active subject enum.

        Returns:
            list[Checkbox]: A list of Checkbox widgets for each subject.
        """
        return [
            Checkbox(subject.value, id=f"checkbox_{i}", classes="checkbox")
            for i, subject in enumerate(self.subject_enum)
        ]

    def clear_fields(self):
        """
        Reset all form inputs and internal state to initial values.
        """
        self.query_one("#name_input", Input).value = ""
        self.query_one("#phone_input", Input).value = ""
        for checkbox in self.query("#subject_list Checkbox"):
            checkbox.value = False

        self.student_name = ""
        self.student_phone = ""
        self.student_grade = EceswaGrade.EGCSE
        self.student_subjects = []

    def add_widget_classes(self):
        """
        Toggle CSS classes on the Save button depending on form validation state.
        """
        save_button = self.query_one("#save_button", Button)
        save_button.remove_class("disable-button", "enable-button")
        save_button.add_class("enable-button" if self.can_save_student_record else "disable-button")

    def validate_form(self):
        """
        Re-evaluate whether all form sections are valid and update UI state.
        """
        self.can_save_student_record = all([
            self.student_name_valid,
            self.student_phone_valid,
            self.student_subjects_valid
        ])
        self.add_widget_classes()

    def on_mount(self):
        """
        Event handler for when the app is mounted. Sets default grade and validates.
        """
        grade_radio = self.query_one("#grade_radio", RadioSet)
        grade_radio.value = EceswaGrade.EGCSE.name 
        self.validate_form()

    def on_input_changed(self, event: Input.Changed):
        """
        React to changes in the name and phone inputs.

        Args:
            event (Input.Changed): Input event emitted when user types in a field.
        """
        if event.input.id == "name_input":
            value = event.value.strip()
            is_valid = 8 <= len(value) <= 100 and bool(self.NAME_REGEX.fullmatch(value))

            event.input.remove_class("valid", "invalid")
            event.input.add_class("valid" if is_valid else "invalid")

            self.student_name_valid = is_valid
            self.student_name = value

        elif event.input.id == "phone_input":
            value = event.value.strip()
            is_valid = bool(self.PHONE_REGEX.fullmatch(value))

            event.input.remove_class("valid", "invalid")
            event.input.add_class("valid" if is_valid else "invalid")

            self.student_phone_valid = is_valid
            self.student_phone = f"+268{value}"

        self.validate_form()

    def on_radio_set_changed(self, event: RadioSet.Changed):
        """
        Update the grade and available subjects when a new grade is selected.

        Args:
            event (RadioSet.Changed): The event triggered when a radio is selected.
        """
        if event.radio_set.id == "grade_radio":
            self.student_grade = EceswaGrade[str(event.pressed.label)]

            if str(event.pressed.label) == EceswaGrade.JC.value:
                self.subject_enum = EceswaJcSubject
            else:
                self.subject_enum = EceswaEgcseSubject

            subject_list_container = self.query_one("#subject_list", HorizontalScroll)
            subject_list_container.remove_children()
            subject_list_container.mount(*self.render_subject_checkboxes())

            first_subject_checkbox = subject_list_container.query(Checkbox)
            first_subject_checkbox.focus()

        self.validate_form()

    def on_input_submitted(self, event: Input.Submitted):
        """
        Handle field-to-field focus change when user presses Enter in inputs.

        Args:
            event (Input.Submitted): Submission event from an Input widget.
        """
        if event.input.id == "name_input":
            self.set_focus(self.query_one("#phone_input", Input))

        if event.input.id == "phone_input":
            self.set_focus(self.query_one("#grade_radio", RadioSet))

        self.validate_form()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """
        Handle selection or deselection of subject checkboxes.

        Args:
            event (Checkbox.Changed): The checkbox change event.
        """
        
        subjects_list = self.query_one("#subject_list", HorizontalScroll)
        checkboxes = subjects_list.query(Checkbox)
        
        self.student_subjects = list({
            str(checkbox.label)
            for checkbox in checkboxes
            if checkbox.value
        })
       
        self.student_subjects_valid = len(self.student_subjects) >= self.SUBJECTS_MIN_THRESHOLD

        subjects_list = self.query_one("#subject_list", HorizontalScroll)
        subjects_list.remove_class("valid", "invalid")
        subjects_list.add_class("valid" if self.student_subjects_valid else "invalid")

        self.validate_form()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Final submission logic triggered by pressing the Save button.

        Args:
            event (Button.Pressed): The press event from the Save button.
        """
        if event.button.id == "save_button" and self.can_save_student_record:
            self.student_record = StudentRecord(
                name=self.student_name,
                phone=self.student_phone,
                grade=self.student_grade.value,
                subjects=self.student_subjects
            )

            self.clear_fields()
            self.exit(self.student_record)
