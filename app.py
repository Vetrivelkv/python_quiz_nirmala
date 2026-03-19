import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st

st.set_page_config(page_title="Python Quiz App", page_icon="🧠", layout="centered")


# -----------------------------
# EMAIL SETTINGS
# -----------------------------
# Replace these with your Gmail details.
# Use a Gmail App Password, not your normal Gmail password.
SENDER_EMAIL = "vetrikvk@gmail.com"
SENDER_APP_PASSWORD = "oyws ogls gopo aipf"
RECEIVER_EMAIL = "vetrivelkvk@gmail.com"


# -----------------------------
# LOAD QUESTIONS
# -----------------------------
with open("questions.json", "r", encoding="utf-8") as file:
    questions = json.load(file)


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
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
    return "You need more practice. Review Python basics, variables, print statements, and data types."


def build_email_body(score, total_questions, percentage, review, wrong_answers):
    lines = [
        "Python Quiz Result",
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


def send_result_email(score, total_questions, percentage, review, wrong_answers):
    subject = "Python Quiz Result"
    body = build_email_body(score, total_questions, percentage, review, wrong_answers)

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        return True, None
    except Exception as error:
        return False, str(error)


# -----------------------------
# SESSION STATE
# -----------------------------
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
st.write(
    "This quiz contains 30 questions about Python basics, Machine Learning/Data Science usage, print statements, variables, and data types."
)

with st.form("quiz_form"):
    for q in questions:
        st.subheader(f"Q{q['id']}. {q['question']}")

        if q["type"] == "single":
            selected = st.radio(
                "Choose one answer:",
                q["options"],
                key=f"question_{q['id']}",
                index=None,
            )
            st.session_state.answers[q["id"]] = [selected] if selected else []

        elif q["type"] == "multiple":
            selected = st.multiselect(
                "Choose all correct answers:",
                q["options"],
                key=f"question_{q['id']}",
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
        st.info("Very good! You have a strong understanding of Python basics.")
    elif percentage >= 50:
        st.warning(
            "Good effort. You understand some concepts, but there is room for improvement."
        )
    else:
        st.warning("Keep practicing. Review Python basics and try again.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Result to Email"):
            result = st.session_state.result_data
            success, error_message = send_result_email(
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
            st.session_state.submitted = False
            st.session_state.answers = {}
            st.session_state.email_sent = False
            st.session_state.result_data = None
            st.rerun()
