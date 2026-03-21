import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st

st.set_page_config(page_title="Python Quiz App", page_icon="🧠", layout="centered")

# -----------------------------
# EMAIL SETTINGS
# -----------------------------
# Replace with your real values.
# Use a Gmail App Password, not your normal Gmail password.
SENDER_EMAIL = "your_email@gmail.com"
SENDER_APP_PASSWORD = "yyxe hzeo mnox hnlx"
RECEIVER_EMAILS = [
    "knkarthi2002@gmail.com",
    "vetrivelkvk@gmail.com",
    "knirmalak99@gmail.com",
]

# -----------------------------
# QUIZ CONFIG
# -----------------------------
QUIZ_FILES = {
    "Quiz 1 - Basics": "questions.json",
    "Quiz 2 - Variables": "2_questions.json",
    "Quiz 3 - Strings and Operators": "3_questions.json",
    "Quiz 4 - Lists": "4_questions.json",
}


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def load_questions(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return json.load(file)


def check_answer(user_answer, correct_answer):
    return sorted(user_answer) == sorted(correct_answer)


def get_review_text(percentage):
    if percentage == 100:
        return "Excellent performance. You answered all questions correctly."
    if percentage >= 75:
        return (
            "Very good performance. You have a strong understanding of Python basics."
        )
    if percentage >= 50:
        return "Good effort. You understand several concepts, but there is still room for improvement."
    return "You need more practice. Review the concepts and try again."


def build_email_body(
    quiz_name, score, total_questions, percentage, review, wrong_answers
):
    lines = [
        "Python Quiz Result",
        "",
        f"This quiz was attended: {quiz_name}",
        "",
        f"Total Questions: {total_questions}",
        f"Correctly Answered Questions: {score}",
        f"Percentage: {percentage:.2f}%",
        "",
        f"Review: {review}",
        "",
        "Question-wise Review:",
        "",
    ]

    if wrong_answers:
        for item in wrong_answers:
            lines.extend(
                [
                    f"Question {item['id']}: {item['question']}",
                    f"Your Answer: {item['user_answer']}",
                    f"Correct Answer: {item['correct_answer']}",
                    "",
                ]
            )
    else:
        lines.append("All answers were correct.")

    return "\n".join(lines)


def send_result_email(
    quiz_name, score, total_questions, percentage, review, wrong_answers
):
    subject = f"Python Quiz Result - {quiz_name}"
    body = build_email_body(
        quiz_name, score, total_questions, percentage, review, wrong_answers
    )

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = ", ".join(RECEIVER_EMAILS)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, message.as_string())
        return True, None
    except Exception as error:
        return False, str(error)


def render_question(question_id, question_text):
    """
    Renders normal question text and code snippet separately.
    Expected JSON format for code questions:
    'What is the output of the following code?\\n\\nprint(\"Hello\")'
    """
    parts = question_text.split("\n\n", 1)

    if len(parts) == 2:
        question_title, code_snippet = parts
        st.markdown(f"### Q{question_id}. {question_title}")
        st.code(code_snippet, language="python")
    else:
        st.markdown(f"### Q{question_id}. {question_text}")


def reset_quiz_state():
    st.session_state.submitted = False
    st.session_state.answers = {}
    st.session_state.email_sent = False
    st.session_state.result_data = None


# -----------------------------
# SESSION STATE
# -----------------------------
if "selected_quiz" not in st.session_state:
    st.session_state.selected_quiz = list(QUIZ_FILES.keys())[0]

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "email_sent" not in st.session_state:
    st.session_state.email_sent = False

if "result_data" not in st.session_state:
    st.session_state.result_data = None


# -----------------------------
# UI
# -----------------------------
st.title("🧠 Python Quiz App")

selected_quiz = st.selectbox(
    "Select Quiz",
    options=list(QUIZ_FILES.keys()),
    index=list(QUIZ_FILES.keys()).index(st.session_state.selected_quiz),
)

if selected_quiz != st.session_state.selected_quiz:
    st.session_state.selected_quiz = selected_quiz
    reset_quiz_state()
    st.rerun()

quiz_file = QUIZ_FILES[st.session_state.selected_quiz]
questions = load_questions(quiz_file)

st.write(f"Currently selected: **{st.session_state.selected_quiz}**")
st.write(f"This quiz contains **{len(questions)}** questions.")

with st.form("quiz_form"):
    for q in questions:
        render_question(q["id"], q["question"])

        if q["type"] == "single":
            selected = st.radio(
                "Choose one answer:",
                q["options"],
                key=f"{st.session_state.selected_quiz}_question_{q['id']}",
                index=None,
            )
            st.session_state.answers[q["id"]] = [selected] if selected else []

        elif q["type"] == "multiple":
            selected = st.multiselect(
                "Choose all correct answers:",
                q["options"],
                key=f"{st.session_state.selected_quiz}_question_{q['id']}",
            )
            st.session_state.answers[q["id"]] = selected

        st.write("---")

    submit_button = st.form_submit_button("Submit Quiz")

if submit_button:
    st.session_state.submitted = True
    st.session_state.email_sent = False


# -----------------------------
# RESULT SECTION
# -----------------------------
if st.session_state.submitted:
    score = 0
    wrong_answers = []

    st.header("Quiz Result")
    st.write(f"**Quiz Attended:** {st.session_state.selected_quiz}")

    for q in questions:
        user_answer = st.session_state.answers.get(q["id"], [])
        correct_answer = q["answer"]

        if check_answer(user_answer, correct_answer):
            score += 1
            st.success(f"Q{q['id']}: Correct")
        else:
            st.error(f"Q{q['id']}: Incorrect")
            st.write(f"**Correct Answer:** {', '.join(correct_answer)}")
            st.write(
                f"**Your Answer:** {', '.join(user_answer) if user_answer else 'No answer selected'}"
            )

            wrong_answers.append(
                {
                    "id": q["id"],
                    "question": q["question"],
                    "user_answer": (
                        ", ".join(user_answer) if user_answer else "No answer selected"
                    ),
                    "correct_answer": ", ".join(correct_answer),
                }
            )

    total_questions = len(questions)
    percentage = (score / total_questions) * 100
    review = get_review_text(percentage)

    st.subheader(f"Final Score: {score} / {total_questions}")
    st.subheader(f"Percentage: {percentage:.2f}%")
    st.write(f"**Review:** {review}")

    st.session_state.result_data = {
        "quiz_name": st.session_state.selected_quiz,
        "score": score,
        "total_questions": total_questions,
        "percentage": percentage,
        "review": review,
        "wrong_answers": wrong_answers,
    }

    if percentage == 100:
        st.balloons()
        st.success("Excellent! You answered all questions correctly.")
    elif percentage >= 75:
        st.info("Very good! You have a strong understanding of this quiz.")
    elif percentage >= 50:
        st.warning(
            "Good effort. You understand some concepts, but there is room for improvement."
        )
    else:
        st.warning("Keep practicing. Review the concepts and try again.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Result to Email"):
            result = st.session_state.result_data
            success, error_message = send_result_email(
                quiz_name=result["quiz_name"],
                score=result["score"],
                total_questions=result["total_questions"],
                percentage=result["percentage"],
                review=result["review"],
                wrong_answers=result["wrong_answers"],
            )

            if success:
                st.session_state.email_sent = True
                st.success("Quiz result email sent successfully.")
            else:
                st.error(f"Failed to send email: {error_message}")

    with col2:
        if st.button("Restart Quiz"):
            reset_quiz_state()
            st.rerun()
