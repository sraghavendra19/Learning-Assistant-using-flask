from flask import Flask, render_template, request, send_file
import cohere
import markdown
import re

app = Flask(__name__)

# Replace with your actual Cohere API key
co = cohere.Client("ExYvetlWFQfA6IXNhtc6wSw6eVdGIqnCa5Exg8jP")

def ask_model(prompt):
    try:
        response = co.chat(message=prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Cohere API error: {e}]"

def generate_content(topic):
    explanation_prompt = f"Explain the topic '{topic}' in simple terms within 30 lines. Make it easy to understand and well-structured. Use markdown formatting for subheadings and examples."
    summary_prompt = f"Summarize the topic '{topic}' in 3-4 lines."
    quiz_prompt = (
        f"Generate 7 multiple-choice questions on the topic '{topic}'. "
        "Each question should have three options labeled A., B., and C., followed by the correct answer on a new line starting with 'Answer:'. "
        "Format:\nQ: Question text\nA. Option 1\nB. Option 2\nC. Option 3\nAnswer: A/B/C"
    )

    # Ask for explanation, convert markdown to HTML
    explanation_raw = ask_model(explanation_prompt)
    explanation_html = markdown.markdown(explanation_raw, extensions=["extra"])

    # Get summary and quiz
    summary = ask_model(summary_prompt)
    quiz_raw = ask_model(quiz_prompt)

    # Resource links
    resources = [
        f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
        f"https://www.khanacademy.org/search?page_search_query={topic.replace(' ', '%20')}",
        f"https://www.coursera.org/search?query={topic.replace(' ', '%20')}",
        f"https://www.edx.org/search?q={topic.replace(' ', '%20')}"
    ]

    quiz = parse_quiz_output(quiz_raw)
    return explanation_html, summary, resources, quiz

def parse_quiz_output(text):
    quiz = []
    questions = re.split(r'\nQ:\s*', text)
    for q in questions:
        if q.strip() == "":
            continue
        lines = q.strip().split('\n')
        question_text = lines[0].strip()
        options = []
        answer = "Not provided"
        for line in lines[1:]:
            if re.match(r'^[A-Ca-c]\.', line.strip()):
                options.append(line.strip())
            elif line.lower().startswith('answer:'):
                answer = line.split(':', 1)[1].strip()
        quiz.append({
            "question": question_text,
            "options": options,
            "answer": answer
        })
    return quiz

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form.get("topic")
        if not topic:
            return render_template("index.html", error="Please enter a topic.")

        explanation, summary, resources, quiz = generate_content(topic)

        with open("output.txt", "w", encoding="utf-8") as f:
            f.write("Explanation:\n" + markdown.markdown(explanation, extensions=["extra"]) + "\n\n")
            f.write("Summary:\n" + summary + "\n\n")
            f.write("Resources:\n" + "\n".join(resources) + "\n\n")
            f.write("Quiz:\n")
            for q in quiz:
                f.write(f"Q: {q['question']}\n")
                for opt in q['options']:
                    f.write(f"{opt}\n")
                f.write(f"Answer: {q['answer']}\n\n")

        return render_template("index.html", topic=topic, explanation=explanation, summary=summary, resources=resources, quiz=quiz)

    return render_template("index.html")

@app.route("/download")
def download():
    return send_file("output.txt", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
