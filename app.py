from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for, flash
import os
import pandas as pd
from jinja2 import Template
from weasyprint import HTML
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'generated_reports'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return redirect('/setup')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        school_info = {
            'school_name': request.form['school_name'],
            'term': request.form['term'],
            'date': request.form['date'],
            'signature': request.form['signature']
        }

        logo = request.files['logo']
        logo_filename = ''
        if logo:
            logo_filename = secure_filename(logo.filename)
            logo.save(os.path.join(UPLOAD_FOLDER, logo_filename))

        grades = request.form.getlist('grade[]')
        mins = request.form.getlist('min_score[]')
        grading_scale = dict(zip(grades, map(int, mins)))

        template_choice = request.form['template']

        request_data = {
            'school_info': school_info,
            'grading_scale': grading_scale,
            'template': template_choice,
            'logo': logo_filename
        }

        return render_template('students.html', data=request_data)
    return render_template('setup.html')

@app.route('/generate', methods=['POST'])
def generate():
    school_info = request.form.get('school_info')
    grading_scale = eval(request.form.get('grading_scale'))
    template = request.form.get('template')
    logo = request.form.get('logo')

    file = request.files['excel']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    df = pd.read_excel(filepath)

    required_columns = {"Full Name",}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        flash(f"Missing required column(s): {', '.join(missing_columns)}", "danger")
        return redirect(url_for('setup'))

    subject_columns = [col for col in df.columns if col not in ["Full Name"]]
    if not subject_columns:
        flash("No subjects found in the Excel file. Add at least one subject column.", "danger")
        return redirect(url_for('setup'))

    scale = sorted(grading_scale.items(), key=lambda x: int(x[1]), reverse=True)

    zip_path = os.path.join(REPORT_FOLDER, 'report_cards.zip')
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for _, row in df.iterrows():
            marks = {}
            for subject in subject_columns:
                marks[subject] = row[subject]
            student_data = {
                'name': row['Full Name'],
                'grade': row['Grade/Class'],
                'subjects': marks
            }

            letter_grades = {}
            for subject, mark in student_data['subjects'].items():
                for grade, min_score in scale:
                    if mark:
                        letter_grades[subject] = grade
                        break
                else:
                    letter_grades[subject] = 'F'

            rendered = render_template('report_template.html',
                                       student=student_data,
                                       grades=letter_grades,
                                       school=eval(school_info),
                                       logo_path=logo)

            output_path = os.path.join(REPORT_FOLDER, f"{student_data['name']}.pdf")
            HTML(string=rendered).write_pdf(output_path)
            zf.write(output_path, arcname=f"{student_data['name']}.pdf")

    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
