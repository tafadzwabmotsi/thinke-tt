from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tqdm import tqdm
import shutil
import os
from typing import Dict, Any
from pylatex import Document, LongTable, MultiColumn, Center
from pylatex.utils import NoEscape, bold, italic
from pylatex.package import Package
from datetime import datetime
from halo import Halo

from constants import BASE_PATH
from lib.utils import LibUtils

class ExamAssigner:
    """
    A class to complete the exam scheduling process by:
        - Creating the student's schedule path directory structure,
        - Copying past paper PDF files from source to the destination folders,
        - Generating a LaTeX document and PDF of the student's exam schedule (not implemented here).
    """

    def __init__(self, exam_schedule: Dict[str, Any]):
        self._exam_schedule = exam_schedule
        self._assign_schedule()

    def _copy_file(self, src: str, dst: str):
        """
        Copy a file from src to dst if it doesn't already exist.
        """
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"Error copying file {src} to {dst}: {e}")
                
    def _assign_schedule(self) -> None:
        """
        Copies all scheduled exam papers to the student's structured folder.
        Uses a progress bar per month with threaded concurrency.
        Skips already existing files and only shows progress when copying is needed.
        """
        student_info = self._exam_schedule["student_info"]
        exam_schedule = self._exam_schedule["exam_schedule"]
        
        def copy_file_with_progress(src: str, dst: str, progress_bar: tqdm):
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"Error copying {src} to {dst}: {e}")
            finally:
                progress_bar.update(1)
      
        os.makedirs(student_info["base_path"], exist_ok=True)

        for month_schedule in exam_schedule:
            year = str(month_schedule["year"])
            month = month_schedule["month"]
            month_schedule_path = os.path.join(student_info["base_path"], year, month)
            os.makedirs(month_schedule_path, exist_ok=True)

            copy_tasks = []

            for daily_schedule in month_schedule["daily_schedules"]:
                day = daily_schedule["day"]
                subject = daily_schedule["subject"]
                papers = daily_schedule["papers"]
                exam_council = daily_schedule["exam_council"]

                schedule_folder = os.path.join(
                    month_schedule_path, 
                    day, 
                    subject,
                    exam_council.title()
                )
                
                os.makedirs(schedule_folder, exist_ok=True)

                for paper in papers:
                    paper_path = paper.get('path')
                    paper_url = paper.get('url')
                    
                    file_name = os.path.basename(paper_path)
                    destination_path = os.path.join(
                        schedule_folder, 
                        file_name
                    )
                    
                    # Save paper to csv
                    LibUtils.save_to_csv(pdf_url=paper_url , pdf_base_path=schedule_folder)

                    if not os.path.exists(destination_path):
                        copy_tasks.append((paper_path, destination_path))

            if copy_tasks:
                with tqdm(
                    total=len(copy_tasks),
                    desc=f"Assigning dates - {month} {year}",
                    unit="file",
                ) as progress_bar:
                    with ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(copy_file_with_progress, src, dst, progress_bar)
                            for src, dst in copy_tasks
                        ]
                        for future in futures:
                            future.result()
    
    def generate_pdf_schedule(self) -> None:
        
        
        def format_date_with_weekday(date_str: str) -> str:
            """Format 'DD-MM-YY' to 'DD-MM-YY (Weekday)'"""
            date_obj = datetime.strptime(date_str, "%d-%m-%y")
            return date_obj.strftime("%d-%m-%y (%a)")

        student_info = self._exam_schedule["student_info"]
        exam_schedule = self._exam_schedule["exam_schedule"]

        # Extract unique subjects
        subject_set = set()
        for ms in exam_schedule:
            for day in ms["daily_schedules"]:
                subject_set.add(day["subject"])
        subjects = sorted(list(subject_set)) # Convert set to sorted list

        # Count total papers
        total_papers = sum(len(day["papers"]) for month in exam_schedule for day in month["daily_schedules"])

        # Get start and end dates
        all_days = [datetime.strptime(day["day"], "%d-%m-%y") for month in exam_schedule for day in month["daily_schedules"]]
        start_date = min(all_days).strftime("%d %B %Y")
        end_date = max(all_days).strftime("%d %B %Y")

        # Document setup with a3paper and 0.5in margin to fit wide tables
        doc = Document(
            documentclass='article', 
            document_options=['a3paper', 'landscape'],  
        )
        # Use Package for geometry options, as it's the more PyLaTeX-idiomatic way
        doc.packages.append(Package('geometry', options=['margin=0.5in']))
        doc.packages.append(Package('amsmath'))
        doc.packages.append(Package('array'))
        doc.packages.append(Package('ragged2e'))
        doc.packages.append(Package('longtable'))
        doc.packages.append(Package('graphicx'))  
        doc.packages.append(NoEscape(r'\pagestyle{empty}'))
        doc.packages.append(NoEscape(r'\raggedbottom'))
        
        # Calculate output path first, as it's needed for relative image path
        output_path = os.path.join(BASE_PATH, 'Output', 'Exam Schedules')
        os.makedirs(output_path, exist_ok=True) 
       
        # Get the directory where the current Python script/class file is located
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the absolute path to your 'images' folder
        images_source_dir = os.path.join(current_script_dir, 'images')
        
        # Full path to the source pen icon
        pen_icon_source_path = os.path.join(images_source_dir, 'write.png')
        
        # Full path where the pen icon will be copied in the output directory
        pen_icon_destination_path = os.path.join(output_path, 'write.png')

        # Copy the pen icon to the output directory
        try:
            shutil.copyfile(pen_icon_source_path, pen_icon_destination_path)
        except FileNotFoundError:
            print(f"Error: Pen icon not found at '{pen_icon_source_path}'. Please ensure the image exists.") 

        # Header block
        # Refactored for true centering by removing \parbox and using \centerline for the rule
        doc.append(NoEscape(r'''
        \begin{center}
            {\huge \textbf{Exam Preparation Schedule}}\\
            \vspace{4mm}
            {\large \textbf{''' + f"{start_date} - {end_date}" + r'''}}\\
            \vspace{4mm}
            \textit{\textbf{Total number of papers: ''' + str(total_papers) + r'''}}\\
            \vspace{8mm}
            {\Large \textbf{''' + student_info['name'] + r'''}}\\
            \vspace{-2mm}
            \centerline{\rule{0.40\textwidth}{0.4pt}}
        \end{center}
        '''))

        doc.append(NoEscape(r'\vspace{5mm}'))
        doc.append(NoEscape(r'\renewcommand{\arraystretch}{2}')) 
        
        column_format = '|>{\\centering\\arraybackslash}m{2.7cm}|' + '|'.join(
            ['>{\\centering\\arraybackslash}m{2.7cm}'] * len(subjects)
        ) + '|'

        
        # Create a longtable per month
        for _, ms in enumerate(exam_schedule):
          
            table = LongTable(column_format)
            
            first_header_text = rf'{{\Large \textit{{\textbf{{{ms["month"]} {ms["year"]}}}}}}}'
            second_header_text = rf'{{\Large \textit{{\textbf{{{ms["month"]} {ms["year"]} (cont.)}}}}}}'
            
            # Define Table Headers and Footers
            # Define the header content for *continuation* pages (\endhead in LaTeX)
            table.add_hline()
            table.add_row([MultiColumn(len(subjects) + 1, align='|c|', data=NoEscape(second_header_text))])
            table.add_hline()
            table.add_row(
                [NoEscape(r'\large \textbf{Date}')] +
                [NoEscape(rf'\large \textbf{{{s}}}') for s in subjects]
            )
            table.add_hline()
            table.append(NoEscape(r'\endhead')) # Marks the end of the continuation header definition

            # Define the header content for the *first* page (\endfirsthead in LaTeX)
            table.add_hline()
            table.add_row([MultiColumn(len(subjects) + 1, align='|c|', data=NoEscape(first_header_text))])
            table.add_hline()
            table.add_row(
                [NoEscape(r'\large \textbf{Date}')] +
                [NoEscape(rf'\large \textbf{{{s}}}') for s in subjects]
            )
            table.add_hline()
            table.append(NoEscape(r'\endfirsthead'))
          
            # Footer for all but last page (if table spans multiple pages within a month)
            table.add_row(
                [MultiColumn(
                    len(subjects) + 1, 
                    align='r', 
                    data=NoEscape(rf'{{\large \textit{{\textbf{{Continued to next page...}}}}}}')
                )]
            )
            table.end_table_footer()
          
            # Footer for the last page of the table (if table spans multiple pages within a month)
            table.add_row(
                [MultiColumn(
                    len(subjects) + 1, 
                    align='r',
                    data=NoEscape(
                        rf'{{\large \textit{{\textbf{{End of schedule for {ms['month']} {ms['year']}}}}}}}'
                    )
                )]
            )
            table.end_table_last_footer()

        
            # Daily rows
            # Now, only the filename is needed because the image has been copied to the output directory
            pen_icon_filename = 'write.png' 
            # Adjust width as needed for your icon size
            pen_icon_command = NoEscape(r'\includegraphics[width=0.8cm, height=0.8cm]{' + pen_icon_filename + r'}')
            
            for day in ms["daily_schedules"]:
                row_data = [''] * len(subjects) # Initialize with empty strings
                subject = day["subject"]
                if subject in subjects:
                    # Place 'X' in the correct subject column
                    row_data[subjects.index(subject)] = pen_icon_command if pen_icon_command else italic(bold('X'))
                
                # Add the date column at the beginning
                table.add_row([bold(italic(format_date_with_weekday(day["day"])))] + row_data)
                table.add_hline()

            # Create the table within a Center environment to ensure the table itself is centered
            with doc.create(Center()) as centered:
                centered.append(table)
        
        
        # Construct the path to which the schedule will be saved
        schedule_path = os.path.join(output_path, f'{student_info['name']} - Exam Preparation Schedule')
        generated_pdf_path = Path(schedule_path).with_suffix('.pdf').resolve()
        
        if generated_pdf_path.exists():
            print(f"◉ Schedule already created for - {student_info['name']}")
            return  # or `return False`, or any value to signal it was skipped

        # Show process on the pdf generation task
        spinner = Halo(
            text=f'Generating exam preparation schedule - {student_info['name']}', 
            color="green",
            text_color="green",
            spinner={
                'interval': 50,
                'frames': ['\\', '|', '/', '_', '-']
            }
        )
        spinner.start()
        
        doc.generate_pdf(schedule_path, compiler='pdflatex', clean_tex=True)
        
        # Delete the pen image after the document has been generated
        os.remove(pen_icon_destination_path)
        
        if not generated_pdf_path.exists():
            raise FileNotFoundError(f"PDF generation failed: {generated_pdf_path} not found")
        
        # Copy the generated pdf file to the student's own directory
        try: 
            student_own_pdf_path = os.path.join(
                    student_info['base_path'],
                    'docs'
            )
            os.makedirs(student_own_pdf_path, exist_ok=True)
            
            destination_file_path = os.path.join(
                student_own_pdf_path,
                generated_pdf_path.name
            )
            shutil.copyfile(
                generated_pdf_path,
                destination_file_path
            )
        except FileNotFoundError:
            print(f"Error: Generated exam schedule not found. Please ensure the file exists.")
        
        spinner.succeed(f"Successfully generated exam preparation schedule - {student_info['name']}")
        spinner.stop()
        
    