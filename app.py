from flask import Flask, render_template, request, redirect, send_from_directory
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/logos/'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        school_name = request.form.get('school_name')
        term = request.form.get('term')
        date = request.form.get('date')
        signature = request.form.get('signature')

        # Handle logo upload
        logo = request.files.get('logo')
        logo_filename = None
        if logo:
            logo_filename = logo.filename
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))

        template_choice = request.form.get('template')

        return f'''
        <h3>Form Submitted Successfully!</h3>
        <p>School: {school_name}</p>
        <p>Term: {term}</p>
        <p>Date: {date}</p>
        <p>Signature: {signature}</p>
        <p>Template Chosen: {template_choice}</p>
        <p>Logo: <img src="/static/logos/{logo_filename}" height="100"></p>
        '''
    return render_template('index.html')
