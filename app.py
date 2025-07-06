import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this in production!

# Configure upload folder for logos
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # max 2MB upload

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get school info
        school_name = request.form.get('school_name', '').strip()
        term = request.form.get('term', '').strip()
        date = request.form.get('date', '').strip()
        signature_text = request.form.get('signature_text', '').strip()
        template = request.form.get('template')
        
        # Save grading scale from hidden JSON input
        grading_scale_json = request.form.get('grading_scale_json', '[]')
        
        # Logo upload handling
        logo_file = request.files.get('logo')
        logo_filename = None
        
        if logo_file and allowed_file(logo_file.filename):
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo_file.save(logo_path)
            logo_filename = filename
        elif logo_file and logo_file.filename != '':
            flash('Invalid file type for logo. Allowed: png, jpg, jpeg, gif')
            return redirect(request.url)
        
        # Save all data in session
        session['school_info'] = {
            'school_name': school_name,
            'term': term,
            'date': date,
            'signature_text': signature_text,
            'template': template,
            'logo_filename': logo_filename
        }
        
        # Save grading scale
        import json
        try:
            grading_scale = json.loads(grading_scale_json)
        except Exception:
            grading_scale = []
        session['grading_scale'] = grading_scale
        
        flash('School info and grading scale saved successfully!')
        return redirect(url_for('index'))
    
    # GET request
    school_info = session.get('school_info', {})
    grading_scale = session.get('grading_scale', [
        {"grade": "A", "minScore": 90},
        {"grade": "B", "minScore": 80},
        {"grade": "C", "minScore": 70}
    ])
    return render_template('index.html', school_info=school_info, grading_scale=grading_scale)

if __name__ == '__main__':
    app.run(debug=True)
