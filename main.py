from flask import Flask, render_template, request, redirect, flash, session
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecretkey"
    load_dotenv()

    def get_db_connection():
        config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "database": os.getenv("DB_NAME", "problem_statement"),
        }
        password = os.getenv("DB_PASSWORD")
        if password:
            config["password"] = password
        try:
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"[DB CONNECTION ERROR] {e}")
        return None

    def get_problem_counts():
        connection = get_db_connection()
        if not connection:
            return {"Option 1": 0, "Option 2": 0, "Option 3": 0, "Option 4": 0}
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT problem_selected, COUNT(*) 
                FROM DETAILS 
                WHERE problem_selected IN ('Option 1', 'Option 2', 'Option 3', 'Option 4')
                GROUP BY problem_selected
            """)
            rows = cursor.fetchall()
            counts = {row[0]: row[1] for row in rows}
            all_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
            return {opt: counts.get(opt, 0) for opt in all_options}
        except Error as e:
            print(f"[COUNTS ERROR] {e}")
            return {"Option 1": 0, "Option 2": 0, "Option 3": 0, "Option 4": 0}
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals() and connection.is_connected():
                connection.close()

    @app.route("/")
    def form1():
        counts = get_problem_counts()
        return render_template("form1.html", counts=counts)

    @app.route("/form2", methods=["POST"])
    def form2():
        problem = request.form.get("problem")
        if not problem:
            flash("Please select a problem statement.")
            return redirect("/")
        
        counts = get_problem_counts()
        if counts.get(problem, 0) >= 20:
            flash("This problem is full. Please choose another.")
            return redirect("/")

        session["problem"] = problem
        return render_template("form2.html", problem=problem)

    @app.route("/submit", methods=["POST"])
    def submit():
        problem = session.pop("problem", None)
        if not problem:
            flash("Session expired. Please start again.", "error")
            return redirect("/")

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not email:
            flash("Name and email are required.", "error")
            return render_template("form2.html", problem=problem)

        if len(name) > 100 or len(email) > 100 or len(phone) > 20:
            flash("Input too long. Name/email ≤100 chars, phone ≤20.", "error")
            return render_template("form2.html", problem=problem)

        counts = get_problem_counts()
        if counts.get(problem, 0) >= 20:
            flash("This problem is now full. Please try another.", "error")
            return redirect("/")

        connection = get_db_connection()
        if not connection:
            flash("❌ Database unavailable.", "error")
            return render_template("form2.html", problem=problem)

        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO DETAILS (Name, Email, Phone, problem_selected)
                VALUES (%s, %s, %s, %s)
            """, (name, email, phone, problem))
            connection.commit()
            flash("✅ Form submitted successfully!", "success")
        except Error as e:
            print(f"[INSERT ERROR] {e}")
            flash("❌ Submission failed. Please try again.", "error")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals() and connection.is_connected():
                connection.close()

        return redirect("/")

    return app

# ✅ Create app instance for WSGI and direct run
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)