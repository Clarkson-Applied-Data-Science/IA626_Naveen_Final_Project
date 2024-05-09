from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'mysql.clarksonmsda.org'),
        user=os.getenv('DB_USER', 'kunan'),
        password=os.getenv('DB_PASSWORD', 'Amma@555555'),
        database=os.getenv('DB_NAME', 'kunan_bigdata_Project')
    )
    return conn


@app.route('/upload/<data_type>', methods=['GET', 'POST'])
def upload_csv(data_type):
    title = f'Upload {data_type.capitalize()} CSV'
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file part')
            return redirect(request.url)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_input = csv.reader(stream)
        conn = get_db_connection()
        cursor = conn.cursor()
        next(csv_input)
        try:
            for row in csv_input:
                cursor.execute(f'''
                    INSERT INTO {data_type}_data (country, date, accumulated, increase)
                    VALUES (%s, %s, %s, %s)
                ''', row)
            conn.commit()
        except Exception as e:
            flash(str(e))
        finally:
            cursor.close()
            conn.close()
        flash('Data inserted successfully')
        return redirect(request.url)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        <form method="POST" action="" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    '''

@app.route('/api/data', methods=['POST'])
def create_data():
    data = request.get_json()
    if not data:
        abort(400, description="No data provided.")

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO covid_data (country, date, accumulated_confirmed, accumulated, accumulated)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (data['country'], data['date'], data['accumulated_confirmed'], data['accumulated_deaths'], data['accumulated_recovered']))
        conn.commit()
        return jsonify({"message": "Data created successfully"}), 201
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()

@app.route('/api/data/<int:data_id>', methods=['GET'])
def get_data_by_id(data_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM covid_data WHERE id = %s"
    try:
        cursor.execute(query, (data_id,))
        result = cursor.fetchone()
        if result:
            return jsonify(result)
        else:
            abort(404, description="Data not found.")
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()

@app.route('/api/data/<int:data_id>', methods=['PUT'])
def update_data(data_id):
    data = request.get_json()
    if not data:
        abort(400, description="No data provided.")

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        UPDATE covid_data
        SET country = %s, date = %s, accumulated_confirmed = %s, accumulated_deaths = %s, accumulated_recovered = %s
        WHERE id = %s
    """
    try:
        cursor.execute(query, (data['country'], data['date'], data['accumulated_confirmed'], data['accumulated_deaths'], data['accumulated_recovered'], data_id))
        if cursor.rowcount == 0:
            abort(404, description="Data not found.")
        conn.commit()
        return jsonify({"message": "Data updated successfully"})
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()

@app.route('/api/data/<int:data_id>', methods=['DELETE'])
def delete_data(data_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM covid_data WHERE id = %s"
    try:
        cursor.execute(query, (data_id,))
        if cursor.rowcount == 0:
            abort(404, description="Data not found.")
        conn.commit()
        return jsonify({"message": "Data deleted successfully"})
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()


@app.route('/api/stats', methods=['GET'])
def get_country_data():
    country = request.args.get('country', None)
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)

    if not start_date or not end_date:
        abort(400, description="start date, and end date are required.")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = f"""
        SELECT 'Confirmed' AS type, SUM(accumulated_confirmed) AS total_accumulated, SUM(increase_of_confirmed) AS total_increase FROM covid_data WHERE country=%s AND date BETWEEN %s AND %s
        UNION
        SELECT 'Deaths', SUM(accumulated_deaths), SUM(increase) FROM death_data WHERE country=%s AND date BETWEEN %s AND %s
        UNION
        SELECT 'Recovered', SUM(accumulated_recovered), SUM(increase) FROM recovered_data WHERE country=%s AND date BETWEEN %s AND %s
    """
    params = [start_date, end_date]

    if country:
        query += " AND country = %s"
        params.append(country)

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        return jsonify(results)
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()


@app.route('/api/data/range', methods=['GET'])
def get_data_range():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')

    if not all([start_date, end_date]):
        abort(400, description="Start date and end date are required parameters.")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    queries = [
        """
        SELECT date, country, 'Confirmed' AS type, accumulated_confirmed AS total
        FROM covid_data
        WHERE date BETWEEN %s AND %s
        """,
        """
        SELECT date, country, 'Deaths' AS type, accumulated_deaths AS total
        FROM death_data
        WHERE date BETWEEN %s AND %s
        """,
        """
        SELECT date, country, 'Recovered' AS type, accumulated_recovered AS total
        FROM recovered_data
        WHERE date BETWEEN %s AND %s
        """
    ]

    if country:
        queries = [q + " AND country = %s" for q in queries]
        params = [start_date, end_date, country] * 3
    else:
        params = [start_date, end_date] * 3

    full_query = " UNION ALL ".join(queries)

    try:
        cursor.execute(full_query, params)
        results = cursor.fetchall()
        return jsonify(results)
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()



@app.route('/api/total_counts', methods=['GET'])
def get_total_counts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 'Confirmed' AS type, SUM(accumulated_confirmed) AS total_accumulated, SUM(increase_of_confirmed) AS total_increase FROM covid_data
        UNION
        SELECT 'Deaths', SUM(accumulated_deaths), SUM(increase) FROM death_data
        UNION
        SELECT 'Recovered', SUM(accumulated_recovered), SUM(increase) FROM recovered_data
    """
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return jsonify(result)
    except mysql.connector.Error as err:
        abort(400, description=str(err))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
