from flask import Flask, render_template, request
import os
import re
import sqlite3
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)

UPLOAD_FOLDER = "resumes"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# database
conn = sqlite3.connect("resume.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates(
    name TEXT,
    email TEXT,
    phone TEXT,
    skills TEXT
)
""")

skills_list = [
    "Python","Java","C","C++",
    "HTML","CSS","JavaScript",
    "SQL","React","Node.js"
]


def read_pdf(file):
    text = ""
    pdf = PdfReader(file)

    for page in pdf.pages:
        t = page.extract_text()
        if t:
            text += t

    return text


def read_docx(file):
    doc = Document(file)

    return "\n".join(
        p.text for p in doc.paragraphs
    )


def get_email(text):
    m = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return m.group() if m else "Not Found"


def get_phone(text):
    m = re.search(r'\+?\d[\d -]{8,12}\d', text)
    return m.group() if m else "Not Found"


def get_name(text):

    for line in text.split("\n")[:5]:

        if len(line.split()) <= 3:
            return line.strip()

    return "Unknown"


def get_skills(text):

    found=[]

    for s in skills_list:

        if s.lower() in text.lower():
            found.append(s)

    return ", ".join(found)


@app.route("/", methods=["GET","POST"])
def home():

    result=None

    if request.method=="POST":

        file=request.files["resume"]

        if file:

            path=os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )

            file.save(path)

            if file.filename.endswith(".pdf"):
                text=read_pdf(path)

            elif file.filename.endswith(".docx"):
                text=read_docx(path)

            else:
                return "Only PDF or DOCX"

            name=get_name(text)
            email=get_email(text)
            phone=get_phone(text)
            skills=get_skills(text)

            cursor.execute(
                "INSERT INTO candidates VALUES(?,?,?,?)",
                (name,email,phone,skills)
            )

            conn.commit()

            result={
                "name":name,
                "email":email,
                "phone":phone,
                "skills":skills
            }

    return render_template(
        "index.html",
        result=result
    )


if __name__=="__main__":
    app.run(debug=True)