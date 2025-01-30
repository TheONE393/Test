from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    total_questions = db.Column(db.Integer)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer)
    correct_answer = db.Column(db.String(1))

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer)
    attempt_number = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer)
    question_id = db.Column(db.Integer)
    user_answer = db.Column(db.String(1))

@app.route('/')
def home():
    chapters = Chapter.query.all()
    return render_template('index.html', chapters=chapters)

@app.route('/chapter/<int:chapter_id>', methods=['GET', 'POST'])
def chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        # Create new attempt
        last_attempt = Attempt.query.filter_by(chapter_id=chapter_id).order_by(Attempt.attempt_number.desc()).first()
        new_attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1
        
        new_attempt = Attempt(
            chapter_id=chapter_id,
            attempt_number=new_attempt_number
        )
        db.session.add(new_attempt)
        db.session.commit()
        
        return redirect(url_for('attempt', attempt_id=new_attempt.id))
    
    return render_template('chapter.html', chapter=chapter)

@app.route('/attempt/<int:attempt_id>', methods=['GET', 'POST'])
def attempt(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    chapter = Chapter.query.get(attempt.chapter_id)
    questions = Question.query.filter_by(chapter_id=chapter.id).all()
    
    if request.method == 'POST':
        # Process answers
        score = 0
        for question in questions:
            user_answer = request.form.get(f'q{question.id}')
            if user_answer == question.correct_answer:
                score += 1
            
            response = Response(
                attempt_id=attempt.id,
                question_id=question.id,
                user_answer=user_answer
            )
            db.session.add(response)
        
        attempt.score = score
        db.session.commit()
        
        return redirect(url_for('results', attempt_id=attempt.id))
    
    return render_template('attempt.html', chapter=chapter, questions=questions, attempt=attempt)

@app.route('/results/<int:attempt_id>')
def results(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    chapter = Chapter.query.get(attempt.chapter_id)
    responses = Response.query.filter_by(attempt_id=attempt_id).all()
    
    # Get question data with correct answers
    response_data = []
    for response in responses:
        question = Question.query.get(response.question_id)
        response_data.append({
            'question_number': responses.index(response) + 1,
            'user_answer': response.user_answer,
            'correct_answer': question.correct_answer
        })
    
    return render_template('results.html', 
                         attempt=attempt,
                         chapter=chapter,
                         response_data=response_data,
                         total_questions=chapter.total_questions)
def insert_sample_data():
    # Run this once to create sample data
    with app.app_context():
        db.create_all()
        
        # Add sample chapter
        chapter = Chapter(name="Sample Chapter", total_questions=5)
        db.session.add(chapter)
        db.session.commit()
        
        # Add sample questions
        answers = ['A', 'B', 'C', 'D', 'A']
        for i in range(5):
            question = Question(
                chapter_id=chapter.id,
                correct_answer=answers[i]
            )
            db.session.add(question)
        
        db.session.commit()
def add_new_chapter():
    with app.app_context():
        new_chapter = Chapter(name="Molecular Biology", total_questions=300)
        db.session.add(new_chapter)
        db.session.commit()
        
        # Add 300 questions (example with dummy answers)
        for i in range(300):
            question = Question(
                chapter_id=new_chapter.id,
                correct_answer='A'  # Set actual correct answers here
            )
            db.session.add(question)
        db.session.commit()
if __name__ == '__main__':
   # insert_sample_data()  # Uncomment first time to create sample data
    app.run(debug=True)