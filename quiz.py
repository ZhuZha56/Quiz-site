import random
import sqlite3
from flask import Flask, redirect, url_for, session, request

app = Flask(__name__)
app.secret_key = 'quiz_secret_key_123'
db_name = 'quiz.sqlite'

def get_quizzes():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM quiz ORDER BY id')
    result = cursor.fetchall()
    conn.close()
    return result

def get_question_after(question_id, quiz_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    query = '''
        SELECT question.id, question.question, question.answer, 
               question.wrong1, question.wrong2, question.wrong3
        FROM question
        JOIN quiz_content ON question.id = quiz_content.question_id
        WHERE quiz_content.quiz_id = ? AND quiz_content.question_id > ?
        ORDER BY quiz_content.question_id
        LIMIT 1
    '''
    cursor.execute(query, [quiz_id, question_id])
    res = cursor.fetchone()
    conn.close()
    
    if res:
        answers = [res[2], res[3], res[4], res[5]]
        random.shuffle(answers)
        return {
            "id": res[0],
            "text": res[1],
            "correct": res[2],
            "answers": answers
        }
    return None

def quiz_form():
    quizzes = get_quizzes()
    options_html = "".join([f'<option value="{q_id}">{q_name}</option>\n' for q_id, q_name in quizzes])
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Выбор викторины</title>
        <link rel="stylesheet" href="{url_for('static', filename='style_quiz.css')}">
    </head>
    <body>
        <body style="background-image: url('{url_for('static', filename='bc2.png')}'); background-size: cover; background-position: center; background-attachment: fixed;">
        <!-- Добавлен контейнер и класс для формы -->
        <div class="container">
            <h2>Выберите викторину:</h2>
            <form method="post" action="/" class="form-quiz">
                <p><select name="quiz_id" class="quiz">{options_html}</select></p>
                <p><input type="submit" value="Отправить" class="btn"></p>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['quiz_id'] = int(request.form.get('quiz_id'))
        session['last_question_id'] = 0
        session['correct_answers'] = 0
        session['total_questions'] = 0
        
        quizzes = get_quizzes()
        for q_id, q_name in quizzes:
            if q_id == session['quiz_id']:
                session['quiz_name'] = q_name
        return redirect(url_for('question_page'))
    return quiz_form()

@app.route('/test', methods=['GET', 'POST'])
def question_page():
    quiz_id = session.get('quiz_id')
    if not quiz_id:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        user_answer = request.form.get('ans')
        correct_answer = session.get('current_correct_answer')
        
        if user_answer and correct_answer:
            session['total_questions'] = session.get('total_questions', 0) + 1
            if user_answer == correct_answer:
                session['correct_answers'] = session.get('correct_answers', 0) + 1

    last_id = session.get('last_question_id', 0)
    question = get_question_after(last_id, quiz_id)
    
    if question is None:
        return redirect(url_for('result_page'))
        
    session['last_question_id'] = question['id']
    session['current_correct_answer'] = question['correct']
    
    answers_html = "".join([
        f"<div class='list'><label><input type='radio' name='ans' value='{ans}' required> {ans}</label></div>" 
        for ans in question['answers']
    ])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Викторина</title>
        <link rel="stylesheet" href="{url_for('static', filename='style_quiz.css')}">
    </head>
    <body>
        <body style="background-image: url('{url_for('static', filename='bc2.png')}'); background-size: cover; background-position: center; background-attachment: fixed;">
        <div class="container">
            <h2>Текущая викторина: {session.get('quiz_name', '')}</h2>
            <h3>Вопрос № {question['id']}</h3>
            <p><b>Текст вопроса:</b> {question['text']}</p>
            <br>
            <form method="post" action="{url_for('question_page')}" class="form-quiz">
                <!-- Варианты ответов выводятся сеткой 2х2 -->
                <div class="radio-buttons">
                    {answers_html}
                </div>
                <br>
                <button type="submit" class="btn">Следующий вопрос</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/result')
def result_page():
    correct = session.get('correct_answers', 0)
    total = session.get('total_questions', 0)
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Результат</title>
        <link rel="stylesheet" href="{url_for('static', filename='style_quiz.css')}">
    </head>
    <body>
        <body style="background-image: url('{url_for('static', filename='bc2.png')}'); background-size: cover; background-position: center; background-attachment: fixed;">
        <div class="container">
            <h2>Викторина окончена!</h2>
            <p class="restext">Ваш результат: {correct} из {total}</p>
            <p>Вы успешно завершили тему: <b>{session.get('quiz_name', '')}</b></p>
            <br>
            <a href="/" class="btn">Пройти викторину заново</a>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
