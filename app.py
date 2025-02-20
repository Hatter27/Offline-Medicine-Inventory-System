from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, jsonify,flash, get_flashed_messages
from datetime import datetime,timedelta
import webbrowser
import csv
from flask import Flask, render_template, request, redirect, url_for, send_file



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Secret key para sa session management

# Function to connect to SQLite database
def connect_db():
    return sqlite3.connect('medicine_inventory.db')

# Initialize Database (Run once)
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create users table (with password hashing support)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')

        # Create medicines table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            expiration_date TEXT NOT NULL,
            category TEXT,
            deleted INTEGER DEFAULT 0
        )''')
        #Check if the Status Exist
        cursor.execute("PRAGMA table_info(medicines)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE medicines ADD COLUMN status INTEGER DEFAULT 1")
            cursor.execute("UPDATE medicines SET status =1 WHERE status IS NULL")

        # Create discounts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_percentage INTEGER NOT NULL
        )''')
       
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_name TEXT NOT NULL,
        quantity_sold INTEGER NOT NULL,
        total_price REAL NOT NULL,
        discounted_price REAL NOT NULL,
        customer_type TEXT NOT NULL,
        cash_given REAL NOT NULL,
        change_amount REAL NOT NULL,
        sale_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
''')
        cursor.execute('''
        CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    medicine_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
''')
      

        conn.commit()
        print("Database initialized successfully.")
        
        

    except sqlite3.Error as e:
        print(f"Database Error: {e}")

    finally:
        cursor.close()
        conn.close()

# Call init_db para sigurado na may database
init_db()

# Homepage
@app.route('/')
def home():
    return render_template('index.html', username=session.get('username'))

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        print("REGISTER DEBUG: Received POST request")
        print(f"REGISTER DEBUG: username={username}, password={password}, confirm_password={confirm_password}")

        if password != confirm_password:
            print("REGISTER ERROR: Passwords do not match")
            return "Passwords do not match!", 400

        hashed_password = generate_password_hash(password)

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            print("REGISTER SUCCESS: User added to database")
        except sqlite3.IntegrityError:
            print("REGISTER ERROR: Username already exists")
            return "Username already exists!", 400
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"LOGIN DEBUG: Username={username}, Password={password}")  # Debugging print

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            stored_password = user[2]  # Dapat hashed password ito
            user_role = user[3]
            user_id = user[0]
            approved = user[4]  # ✅ Kukunin natin ang `approved` column (index 4)

            print(f"LOGIN DEBUG: Stored Hashed Password={stored_password}, Role={user_role}, Approved={approved}")  # Debugging print

            if approved == 0:  # ✅ Check kung hindi pa approved
                print("LOGIN FAILED: Account not approved")
                return render_template('login.html', error="Your account is pending approval. Please wait for admin confirmation.")

            if check_password_hash(stored_password, password):  # Check hashed password
                print("LOGIN SUCCESS: Correct password")
                session['user_id'] = user_id  # Store user_id in session
                session['username'] = username
                session['role'] = user_role  # ✅ Store role in session
                return redirect('/')
            else:
                print("LOGIN FAILED: Incorrect password")
                return render_template('login.html', error="Incorrect password. Please try again.")
        else:
            print("LOGIN FAILED: Username not found")
            return render_template('login.html', error="Account not registered. Please register first.")

    return render_template('login.html')

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    conn = sqlite3.connect('medicine_inventory.db')
    c = conn.cursor()
    c.execute("UPDATE users SET approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash('User has been approved successfully!', 'success')
    return redirect(url_for('admin_panel'))


# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)  # Tanggalin ang session na nagpapa-enable ng Admin Panel button
    return redirect(url_for('home'))  

@app.route('/delete_medicine/<int:id>', methods=['POST'])
def delete_medicine(id):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Kunin ang kasalukuyang timestamp
        deleted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Hanapin ang gamot
        cursor.execute("SELECT * FROM medicines WHERE id = ?", (id,))
        medicine = cursor.fetchone()

        if not medicine:
            flash("Gamot ay hindi natagpuan!", "danger")
            return redirect(url_for('add_medicine'))  # Redirect after error

        # I-update ang status ng gamot bilang deleted at idagdag ang deleted_at timestamp
        cursor.execute("""
        UPDATE medicines SET status = 0, deleted_at = ? WHERE id = ?
        """, (deleted_at, id))

        conn.commit()

        flash("Medicine has been deleted successfully", "success")
        return redirect(url_for('add_medicine'))  # Redirect after deletion

    except sqlite3.Error as e:
        flash("May error sa pag-delete ng gamot.", "danger")
        return redirect(url_for('add_medicine'))  # Redirect after error

@app.route('/restore_medicine/<int:id>', methods=['POST'])
def restore_medicine(id):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Kumuha ng user_id mula sa session (kung naka-login)
        user_id = session.get('user_id')

        # I-update ang status at tanggalin ang deleted_at timestamp
        cursor.execute("""
            UPDATE medicines SET status = 1, deleted_at = NULL WHERE id = ?
        """, (id,))
        conn.commit()

        # Mag-log ng action sa logs table
        action = 'Restore Medicine'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO logs (user_id, action, medicine_name, timestamp)
            SELECT ?, ?, name, ? FROM medicines WHERE id = ?
        """, (user_id, action, timestamp, id))
        conn.commit()

        flash("Medicine has been restored successfully", "success")
    except sqlite3.Error as e:
        flash("Error restoring medicine!", "danger")
    finally:
        conn.close()

    return redirect(url_for('deleted_medicines'))


@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        expiration_date = request.form['expiration_date']
        category = request.form['category']

        # Kumuha ng user_id mula sa session (kung naka-login)
        user_id = session.get('user_id')

        # Step 1: Check kung may existing na gamot
        cursor.execute("SELECT * FROM medicines WHERE name = ?", (name,))
        existing_medicine = cursor.fetchone()

        if existing_medicine:
            if existing_medicine[7] == 1:
                flash("Duplicate medicine is not allowed!", "danger")
                conn.close()
                return redirect(url_for('add_medicine'))

            elif existing_medicine[7] == 0:
                cursor.execute("UPDATE medicines SET quantity = ?, price = ?, expiration_date = ?, category = ?, status = 1 WHERE name = ?",
                               (quantity, price, expiration_date, category, name))
                conn.commit()
                flash("Medicine restored successfully!", "success")
                conn.close()
                return redirect(url_for('add_medicine'))

        else:
            cursor.execute('INSERT INTO medicines (name, quantity, price, expiration_date, category, status) VALUES (?, ?, ?, ?, ?, 1)',
                           (name, quantity, price, expiration_date, category))
            conn.commit()
            flash("Medicine added successfully!", "success")

            # Log the action of adding medicine to the logs table
            action = 'Add Medicine'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO logs (user_id, action, medicine_name, timestamp) VALUES (?, ?, ?, ?)",
                           (user_id, action, name, timestamp))
            conn.commit()

    cursor.execute("SELECT * FROM medicines WHERE status = 1")
    medicines = cursor.fetchall()

    conn.close()
    return render_template('add_medicine.html', medicines=medicines)



# View Medicines (Para makita lahat ng gamot)
@app.route('/view_medicines')
def view_medicines():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM medicines WHERE deleted = 0')
    medicines = cursor.fetchall()
    conn.close()
    
    return render_template('view_medicines.html', medicines=medicines)

@app.route('/manage_discounts')
def manage_discounts():
    conn = sqlite3.connect('medicine_inventory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, name, price, quantity FROM medicines WHERE deleted = 0 AND status = 1")  
    medicines = cursor.fetchall()
    conn.close()
    return render_template('manage_discounts.html', medicines=medicines)

@app.route('/get_medicine_price')
def get_medicine_price():
    medicine_name = request.args.get('medicine')

    if not medicine_name:
        return jsonify({"error": "No medicine name provided"}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM medicines WHERE name = ? AND status = 1", (medicine_name,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({"price": result[0]})
    else:
        return jsonify({"error": "Medicine not found"}), 404
    
    
def get_db_connection():
    conn = sqlite3.connect('medicine_inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route para i-update ang stock ng medicine
@app.route('/update_stock', methods=['POST'])
def update_stock():
    try:
        medicine_name = request.form['medicine']
        quantity_sold = int(request.form['quantity'])

        conn = get_db_connection()
        cursor = conn.cursor()

        # Kunin ang kasalukuyang quantity
        cursor.execute("SELECT quantity FROM medicines WHERE name = ?", (medicine_name,))
        result = cursor.fetchone()

        if result:
            current_quantity = result[0]
            if current_quantity >= quantity_sold:
                new_quantity = current_quantity - quantity_sold

                # I-update ang stock quantity sa database
                cursor.execute("UPDATE medicines SET quantity = ? WHERE name = ?", (new_quantity, medicine_name))
                conn.commit()
                conn.close()

                return jsonify({"status": "success", "message": "Stock updated successfully."})
            else:
                conn.close()
                return jsonify({"status": "error", "message": "Not enough stock available."})
        else:
            conn.close()
            return jsonify({"status": "error", "message": "Medicine not found."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# View Deleted Medicines (Para sa Restore Function)
@app.route('/deleted_medicines')
def deleted_medicines():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Query to get all medicines where status = 0 (deleted)
        cursor.execute("SELECT * FROM medicines WHERE status = 0")
        deleted_medicines = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('deleted_medicines.html', deleted_medicines=deleted_medicines)

    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return render_template('deleted_medicines.html', deleted_medicines=[])

@app.route('/delete_permanently/<int:id>', methods=['POST'])
def delete_permanently(id):
    db = sqlite3.connect("medicine_inventory.db")
    cursor = db.cursor()

    # Kumuha ng user_id mula sa session (kung naka-login)
    user_id = session.get('user_id')
    if not user_id:
        flash("User not logged in. Please log in first.", "danger")
        return redirect(url_for('login'))  # Redirect to login kung walang user_id

    # Kunin ang pangalan ng gamot bago ito idelete (for logging)
    cursor.execute("SELECT name FROM medicines WHERE id = ?", (id,))
    medicine = cursor.fetchone()

    if medicine:
        # Permanent delete sa database (only if status = 0)
        cursor.execute("DELETE FROM medicines WHERE id = ? AND status = 0", (id,))
        db.commit()

        # Mag-log ng delete action sa logs table
        action = 'Delete Medicine Permanently'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO logs (user_id, action, medicine_name, timestamp) VALUES (?, ?, ?, ?)",
                       (user_id, action, medicine[0], timestamp))
        db.commit()

        flash(f"Medicine '{medicine[0]}' permanently deleted.", "success")
    else:
        flash("Medicine not found.", "danger")

    db.close()
    return redirect(url_for('deleted_medicines'))  # Redirect to a page for deleted medicines (or another page)


@app.route('/view_alerts')
def view_alerts():
    conn = connect_db()
    cursor = conn.cursor()

    # Kunin ang petsa ngayon
    today = datetime.now().date()
    threshold_date = today + timedelta(days=7)  # Halimbawa: 7 araw bago mag-expire

    # Kunin ang mga gamot na malapit nang mag-expire
    cursor.execute("SELECT name, expiration_date, quantity FROM medicines WHERE expiration_date <= ? AND quantity > 0", (threshold_date,))
    near_expiry = cursor.fetchall()

    # Kunin ang mga gamot na mababa na ang stock (halimbawa: <5 piraso)
    cursor.execute("SELECT name, expiration_date, quantity FROM medicines WHERE quantity < 5 AND quantity > 0")
    low_stock = cursor.fetchall()

    conn.close()

    return render_template('view_alerts.html', near_expiry=near_expiry, low_stock=low_stock)

@app.route('/view_deleted_medicines')
def view_deleted_medicines():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Hanapin ang mga deleted na gamot (status = 0)
        cursor.execute("SELECT * FROM medicines WHERE status = 0")
        deleted_medicines = cursor.fetchall()

        return render_template('deleted_medicines.html', deleted_medicines=deleted_medicines)

    except sqlite3.Error as e:
        flash("May error sa pagkuha ng deleted medicines.", "danger")
        return redirect(url_for('add_medicine'))  # Redirect kahit may error
    
@app.route('/edit_medicine', methods=['POST'])
def edit_medicine():
    conn = connect_db()
    cursor = conn.cursor()

    # Kumuha ng user_id mula sa session (kung naka-login)
    user_id = session.get('user_id')

    # Kumuha ng mga field values mula sa form
    medicine_id = request.form['medicine_id']
    name = request.form['name']
    quantity = request.form['quantity']
    price = request.form['price']
    expiration_date = request.form['expiration_date']
    category = request.form['category']

    # Update medicine record
    cursor.execute("""
        UPDATE medicines 
        SET name = ?, quantity = ?, price = ?, expiration_date = ?, category = ? 
        WHERE id = ?
    """, (name, quantity, price, expiration_date, category, medicine_id))

    # Mag-log ng action sa logs table
    action = 'Edit Medicine'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO logs (user_id, action, medicine_name, timestamp)
        SELECT ?, ?, name, ? FROM medicines WHERE id = ?
    """, (user_id, action, timestamp, medicine_id))

    conn.commit()
    conn.close()

    flash("Medicine updated successfully!", "success")
    return redirect(url_for('add_medicine'))


DATABASE = "medicine_inventory.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    medicine_name = request.form.get('medicine')
    quantity_sold = request.form.get('quantity')
    total_price = request.form.get('totalPrice')  # Original price
    discounted_price = request.form.get('discountedPrice')  # Discounted price
    customer_type = request.form.get('customerType')  # Senior, PWD, Regular
    cash_given = request.form.get('cashGiven')  # Binayad ng customer
    change_amount = request.form.get('change')  # Sukli
    sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp

    # Debug: I-print ang customer type para makita kung ano ang ipinasang value
    print("🔍 DEBUG: Customer Type:", customer_type)

    # Kung walang data na naipasa
    if not all([medicine_name, quantity_sold, total_price, discounted_price, customer_type, cash_given, change_amount]):
        print("❌ ERROR: May kulang sa data!")
        return jsonify({"status": "error", "message": "May kulang na data"}), 400  # HTTP 400 Bad Request

    try:
        quantity_sold = int(quantity_sold)
        total_price = float(total_price)
        discounted_price = float(discounted_price)
        cash_given = float(cash_given)
        change_amount = float(change_amount)
    except ValueError:
        print("❌ ERROR: Mali ang format ng numerical values!")
        return jsonify({"status": "error", "message": "Maling format ng data"}), 400

    # Kung Regular na customer, walang discount
    if customer_type == 'regular':
        discounted_price = total_price  # Walang discount para sa Regular na customer
        action = 'Sale without Discount'
    else:
        action = f'Apply Discount for {customer_type.title()}'  # Halimbawa: 'Apply Discount for Senior Citizen'

    # Debug: I-print ang action para makita kung anong action ang nakalagay
    print("Action na ipo-log:", action)

    conn = sqlite3.connect('medicine_inventory.db')
    cursor = conn.cursor()

    try:
        # ✅ INSERT sa sales table (kasama na ang discount kung applicable)
        cursor.execute("""
            INSERT INTO sales (medicine_name, quantity_sold, total_price, discounted_price, customer_type, cash_given, change_amount, sale_date, user_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (medicine_name, quantity_sold, total_price, discounted_price, customer_type, cash_given, change_amount, sale_date, session.get('user_id')))

        # ✅ UPDATE sa medicines table (babawasan ang stock)
        cursor.execute("UPDATE medicines SET quantity = quantity - ? WHERE name = ?",
                       (quantity_sold, medicine_name))

        # Log the action sa logs table
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO logs (user_id, action, medicine_name, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session.get('user_id'), action, medicine_name, timestamp))

        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ ERROR: Error sa database: {e}")
        return jsonify({"status": "error", "message": "Error sa database"}), 500
    finally:
        conn.close()

    print("✅ SUCCESS: Nasave sa database!")

    # **✔️ RETURN JSON RESPONSE para hindi mag-error ang `fetch`**
    return jsonify({"status": "success", "message": "Transaction saved successfully!"})




@app.route('/view_sales')
def view_sales():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales")
    sales = cursor.fetchall()
    conn.close()
    return render_template("view_sales.html", sales=sales)

@app.route('/revenue', methods=['GET'])
def revenue():
    # Kunin ang date mula sa URL parameter, kung wala, gamitin ang today_date
    date_param = request.args.get('date')
    today_date = date_param if date_param else datetime.now().strftime('%Y-%m-%d')

    # Connect sa database
    conn = sqlite3.connect('medicine_inventory.db')
    cursor = conn.cursor()

    # Kunin ang total sales sa napiling petsa
    cursor.execute("SELECT SUM(discounted_price) FROM sales WHERE DATE(sale_date) = ?", (today_date,))
    total_revenue = cursor.fetchone()[0] or 0  # Default to 0 kung walang sales

    conn.close()
    
    return render_template('revenue.html', total_revenue=total_revenue, selected_date=today_date)

@app.route('/admin_panel')
def admin_panel():
    # Siguraduhin na admin lang ang makakapasok
    if 'role' not in session or session['role'] != 'admin':
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('dashboard'))  # Babalik sa dashboard

    conn = connect_db()
    cursor = conn.cursor()

    # Kunin lahat ng users para makita sa admin panel
    cursor.execute("SELECT id, username, password, role, approved  FROM users")
    users = cursor.fetchall()

    # Kunin din lahat ng logs para ma-track ang activities
    cursor.execute("SELECT logs.id, users.username, logs.action, logs.medicine_name, logs.timestamp FROM logs JOIN users ON logs.user_id = users.id ORDER BY logs.timestamp DESC")
    logs = cursor.fetchall()

    conn.close()
    return render_template('admin_panel.html', users=users, logs=logs)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Delete user by user_id from the users table
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash("User account has been deleted successfully.", "success")
    except sqlite3.Error as e:
        flash("Error deleting user account.", "danger")
    finally:
        conn.close()

    return redirect(url_for('admin_panel'))  # Redirect back to the admin panel

@app.route('/delete_log/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    # Connect to the database
    conn = sqlite3.connect('medicine_inventory.db')
    cursor = conn.cursor()

    try:
        # Delete the log entry from the logs table
        cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))
        conn.commit()
        flash("Log entry deleted successfully.", "success")
    except Exception as e:
        print("❌ Error deleting log:", e)
        flash("Failed to delete log entry.", "danger")
    finally:
        conn.close()

    # Redirect back to the admin panel after deletion
    return redirect(url_for('admin_panel'))

def connect_db():
    return sqlite3.connect('medicine_inventory.db')

@app.route('/export_csv')
def export_csv():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Kunin ang lahat ng gamot sa database
    cursor.execute("SELECT id, name, quantity, price, expiration_date, category, deleted, status FROM medicines")  # Palitan ang 'medicines' kung iba ang table name mo
    medicines = cursor.fetchall()
    
    conn.close()
    
    # Lumikha ng CSV file
    csv_filename = "medicine_inventory.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id", "name", "Quantity", "price","expiration_date","category", "deleted", "status",])  # Palitan base sa table columns mo
        writer.writerows(medicines)

    return send_file(csv_filename, as_attachment=True)

@app.route('/export_sales_csv')
def export_sales_csv():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, medicine_name, quantity_sold, total_price, discounted_price, customer_type, cash_given, change_amount, sale_date FROM sales")
    sales = cursor.fetchall()
    conn.close()

    csv_filename = "sales_report.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Medicine Name", "Quantity Sold", "Total Price", "Discounted Price", "Customer Type", "Cash Given", "Change Amount", "Transaction Date"])

        for row in sales:
            formatted_row = list(row)

            # I-check kung may laman at tamang format ang transaction_date
            if row[8]:  # Ensure it's not None
                try:
                    # Convert string date to correct format
                    transaction_date = datetime.strptime(row[8], "%Y-%m-%d %H:%M:%S")  
                    formatted_row[8] = transaction_date.strftime("%Y-%m-%d %H:%M:%S")  # Convert properly
                except ValueError:
                    formatted_row[8] = row[8]  # If already in correct format, use as is
            else:
                formatted_row[8] = "N/A"  # If null, put "N/A"

            writer.writerow(formatted_row)

    return send_file(csv_filename, as_attachment=True)

@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    # Logic para i-delete ang sale sa database gamit ang sale_id
    connection = sqlite3.connect('medicine_inventory.db')
    cursor = connection.cursor()
    cursor.execute("DELETE FROM sales WHERE id=?", (sale_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('view_sales'))  # Redirect after deletion

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/") 


def connect_db():
    return sqlite3.connect('medicine_inventory.db')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    open_browser()
    app.run(debug=True)