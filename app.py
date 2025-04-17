@app.route("/doctors")
def doctors_page():
    return render_template("doctors.html")

@app.route("/get_doctors_list")
def get_doctors_list():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT doctor_id, name, specialty FROM doctors")
        doctors = cur.fetchall()

        doctor_list = []
        for doc in doctors:
            doctor_list.append({
                "doctor_id": doc[0],
                "name": doc[1],
                "specialty": doc[2],
                "morning": True,
                "afternoon": False,
                "evening": True,
                "wait_time": random.choice([15, 30, 45])  # Dummy random wait time
            })

        cur.close()
        conn.close()

        return jsonify(doctor_list)

    except Exception as e:
        print("Doctors list fetch error:", e)
        return jsonify({"error": str(e)}), 500
