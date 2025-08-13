from pathlib import Path
import shutil
import os
import time
from pylatex import Document, LongTable, MultiColumn, Center
from pylatex.utils import NoEscape, bold, italic
from pylatex.package import Package
from datetime import datetime
from lib.constants import BASE_DIR
from lib.typing.domain.schedule import ExamSchedule, SchedulePaper
from lib.utils import LibUtils

class ScheduleGenerator:
   
    def __init__(self, schedule: ExamSchedule):
        self._schedule = schedule
                
    def save_schedule_to_disk(self) -> None:
        for month_schedule in self._schedule.monthly_schedules:
            for daily_schedule in month_schedule.daily_schedules:
                for p in daily_schedule.papers:
                    p.dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    LibUtils.copy_file(p.src_path, p.dest_path)
    
    def generate_pdf_schedule(self) -> None:
        schedule = self._schedule
        
        # Guarantee that the generated pdf parent dir exist
        schedule.generated_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            
        # Extract unique subjects
        subject_set = {
            ds.subject
            for ms in schedule.monthly_schedules
            for ds in ms.daily_schedules
        }
        subjects = list(subject_set)

        # Count total papers
        total_papers = sum(
            len(ds.papers) 
            for ms in schedule.monthly_schedules
            for ds in ms.daily_schedules
        )

        # Get start and end dates for the schedule
        all_days = [
            datetime.strptime(ds.day, "%d-%m-%y") 
            for ms in schedule.monthly_schedules 
            for ds in ms.daily_schedules
        ]
       
        start_date = min(all_days).strftime("%d %B %Y")
        end_date = max(all_days).strftime("%d %B %Y")

        # Document setup with a3paper and 0.5in margin to fit wide tables
        doc = Document(
            documentclass='article', 
            document_options=['a3paper', 'landscape'],  
        )
        doc.packages.append(Package('geometry', options=['margin=0.5in']))
        doc.packages.append(Package('amsmath'))
        doc.packages.append(Package('array'))
        doc.packages.append(Package('ragged2e'))
        doc.packages.append(Package('longtable'))
        doc.packages.append(Package('graphicx'))  
        doc.packages.append(NoEscape(r'\pagestyle{empty}'))
        doc.packages.append(NoEscape(r'\raggedbottom'))

        # Copy the pen icon to the output directory
        cwd = Path(__file__).resolve().parent
        img_src = cwd / 'images'
        icon_src = img_src / 'write.png'
        icon_dest = schedule.generated_pdf_path.parent / 'write.png'
        LibUtils.copy_file(icon_src, icon_dest)
    
        # Header block
        doc.append(NoEscape(r'''
        \begin{center}
            {\huge \textbf{Exam Preparation Schedule}}\\
            \vspace{4mm}
            {\large \textbf{''' + f"{start_date} - {end_date}" + r'''}}\\
            \vspace{4mm}
            \textit{\textbf{Total number of papers: ''' + str(total_papers) + r'''}}\\
            \vspace{8mm}
            {\Large \textbf{''' + schedule.student_info.name + r'''}}\\
            \vspace{-2mm}
            \centerline{\rule{0.40\textwidth}{0.4pt}}
        \end{center}
        '''))
        doc.append(NoEscape(r'\vspace{5mm}'))
        doc.append(NoEscape(r'\renewcommand{\arraystretch}{2}')) 
        
        column_format = '|>{\\centering\\arraybackslash}m{2.5cm}|' + '|'.join(
            ['>{\\centering\\arraybackslash}m{2.7cm}'] * len(subjects)
        ) + '|'

        # Sort monthly schedules by the earliest date inside each month
        sorted_months = sorted(
            schedule.monthly_schedules,
            key=lambda ms: min(datetime.strptime(ds.day, "%d-%m-%y") for ds in ms.daily_schedules)
        )

        # Create a longtable per month
        for ms in sorted_months:
            table = LongTable(column_format)
            
            first_header_text = rf'{{\Large \textit{{\textbf{{{ms.month} {ms.year}}}}}}}'
            second_header_text = rf'{{\Large \textit{{\textbf{{{ms.month} {ms.year} (cont.)}}}}}}'
            
            # Define Table Headers and Footers
            table.add_hline()
            table.add_row([MultiColumn(len(subjects) + 1, align='|c|', data=NoEscape(second_header_text))])
            table.add_hline()
            table.add_row(
                [NoEscape(r'\large \textbf{Date}')] +
                [NoEscape(rf'\large \textbf{{{s}}}') for s in subjects]
            )
            table.add_hline()
            table.append(NoEscape(r'\endhead'))

            table.add_hline()
            table.add_row([MultiColumn(len(subjects) + 1, align='|c|', data=NoEscape(first_header_text))])
            table.add_hline()
            table.add_row(
                [NoEscape(r'\large \textbf{Date}')] +
                [NoEscape(rf'\large \textbf{{{s}}}') for s in subjects]
            )
            table.add_hline()
            table.append(NoEscape(r'\endfirsthead'))

            table.add_row(
                [MultiColumn(
                    len(subjects) + 1, 
                    align='r', 
                    data=NoEscape(rf'{{\large \textit{{\textbf{{Continued to next page...}}}}}}')
                )]
            )
            table.end_table_footer()
        
            table.add_row(
                [MultiColumn(
                    len(subjects) + 1, 
                    align='r',
                    data=NoEscape(
                        rf'{{\large \textit{{\textbf{{End of schedule for {ms.month} {ms.year}}}}}}}'
                    )
                )]
            )
            table.end_table_last_footer()

            # Daily rows sorted by date
            icon_filename = 'write.png'
            icon_cmd = NoEscape(r'\includegraphics[width=0.8cm, height=0.8cm]{' + icon_filename + r'}')
            
            sorted_days = sorted(
                ms.daily_schedules,
                key=lambda d: datetime.strptime(d.day, "%d-%m-%y")
            )

            for ds in sorted_days:
                row_data = [''] * len(subjects)
                if ds.subject in subjects:
                    row_data[subjects.index(ds.subject)] = icon_cmd or italic(bold('X'))

                table.add_row([bold(italic(LibUtils.format_date_with_weekday(ds.day)))] + row_data)
                table.add_hline()

            # Center the table
            with doc.create(Center()) as centered:
                centered.append(table)
                
        doc.generate_pdf(
            schedule.generated_pdf_path, 
            compiler='pdflatex', 
            clean_tex=True
        )
        
        time.sleep(1)
        os.remove(icon_dest)
