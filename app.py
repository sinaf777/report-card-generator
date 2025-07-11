from flask import Flask, render_template, request, redirect, send_file, url_for, flash
import os
import pandas as pd
from weasyprint import HTML
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'generated_reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('setup.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Collect school info
    school_info = {
        'school_name': request.form['school_name'],
        'term': request.form['term'],  # This will be either "1st Semester" or "2nd Semester"
        'date': request.form['date']
    }

    # Get uploaded Excel file
    file = request.files['excel']
    if not file:
        flash("No Excel file uploaded.", "danger")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Read Excel
    df = pd.read_excel(filepath)

    # Validation
    required_columns = {"Full Name", "Grade/Class"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        flash(f"Missing column(s): {', '.join(missing_columns)}", "danger")
        return redirect(url_for('index'))

    subject_columns = [col for col in df.columns if col not in ["Full Name", "Grade/Class"]]
    if not subject_columns:
        flash("No subject columns found in the Excel file.", "danger")
        return redirect(url_for('index'))

    # Create zip
    zip_path = os.path.join(REPORT_FOLDER, 'report_cards.zip')
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for _, row in df.iterrows():
            subject_data = []
            total_first = total_second = total_avg = 0

            for subject in subject_columns:
                try:
                    val = str(row[subject])
                    scores = val.split('/')
                    first = int(scores[0]) if scores[0].isdigit() else 0
                    second = int(scores[1]) if len(scores) > 1 and scores[1].isdigit() else 0
                except:
                    first, second = 0, 0
                
                avg = (first + second) / 2 if (first != 0 or second != 0) else 0
                
                # Store all values but we'll control display in the template
                subject_data.append({
                    'name': subject,
                    'first': first,
                    'second': second,
                    'average': round(avg, 2) if avg != 0 else ""
                })

                total_first += first
                total_second += second
                total_avg += avg if avg != 0 else 0

            student_data = {
                'name': row['Full Name'],
                'grade': row['Grade/Class'],
                'subjects': subject_data,
                'total_first': total_first,
                'total_second': total_second,
                'total_average': round(total_avg, 2) if total_avg != 0 else "",
                'avg_first': round(total_first / len(subject_columns), 2) if len(subject_columns) > 0 else "",
                'avg_second': round(total_second / len(subject_columns), 2) if len(subject_columns) > 0 else "",
                'avg_overall': round(total_avg / len(subject_columns), 2) if len(subject_columns) > 0 else "",
                'rank_first': '___',
                'rank_second': '___',
                'rank_average': '___',
                'conduct': '___'
            }

            # Render template
            rendered = render_template('report_template.html', student=student_data, school=school_info)
            output_path = os.path.join(REPORT_FOLDER, f"{student_data['name']}.pdf")
            HTML(string=rendered).write_pdf(output_path)
            zf.write(output_path, arcname=f"{student_data['name']}.pdf")

    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)