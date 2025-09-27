from flask import Flask, request, jsonify, session, redirect, render_template, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pymysql
import bcrypt
import logging

# 設置日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/login": {"origins": "*"}, r"/register": {"origins": "*"}})

app.config['JWT_SECRET_KEY'] = 'supersecret'
app.secret_key = 'another_secret'
jwt = JWTManager(app)
app.logger = logging.getLogger(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'eva100422',
    'database': 'eco_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        connection = pymysql.connect(**db_config)
        return connection
    except Exception as e:
        app.logger.error(f"數據庫連接錯誤: {str(e)}")
        raise

# ========= HTML 頁面 =========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login-page')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/backmanament-page')
def backmanament_page():
    return render_template('backmanament.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/register-page')
def register_page():
    return render_template('register.html')

@app.route('/shop-page')
def shop_page():
    return render_template('shop.html')

@app.route('/goals-page')
def goals_page():
    return render_template('goals.html')

@app.route('/howto-page')
def howto_page():
    return render_template('howto.html')

@app.route('/about-page')
def about_page():
    return render_template('about.html')

@app.route('/contact-page')
def contact_page():
    return render_template('contact.html')

@app.route('/faq-page')
def faq_page():
    return render_template('faq.html')

@app.route('/profile-page')
def profile_page():
    return render_template('profile_1.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login-page')
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/', code=302)

# API 路由：根據 username 獲取使用者資料
@app.route('/api/users', methods=['GET'])
def get_user():
    username = request.args.get('username')
    if not username:
        return jsonify({'message': 'Username parameter is missing'}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = "SELECT username, points, address, birthday, email, phone FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            return jsonify(user), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'message': 'Error fetching user data', 'error': str(e)}), 500

# ========= 註冊 API =========
@app.route('/register', methods=['POST'])
def register():
    try:
        if not request.is_json:
            app.logger.warning("註冊請求未使用JSON格式")
            return jsonify({'status': 'fail', 'message': '請使用JSON格式提交數據'}), 400
            
        data = request.get_json()
        if data is None:
            app.logger.warning("無法解析JSON數據")
            return jsonify({'status': 'fail', 'message': '無法解析請求數據'}), 400
            
        app.logger.info(f"收到註冊數據: {data}")

        required_fields = ['username', 'email', 'phone', 'password', 'address', 'birthday']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            app.logger.warning(f"缺少必要欄位: {missing_fields}")
            return jsonify({
                'status': 'fail', 
                'message': f'請提供必要欄位: {", ".join(missing_fields)}'
            }), 400

        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        address = data.get('address')
        birthday = data.get('birthday')

        if not password:
            return jsonify({'status': 'fail', 'message': '密碼不能為空'}), 400

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, email))
                if cursor.fetchone():
                    return jsonify({'status': 'fail', 'message': '使用者名稱或Email已存在'}), 409

                try:
                    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    app.logger.debug(f"生成的密碼雜湊: {hashed_pw[:10]}... (長度: {len(hashed_pw)})")
                except Exception as hash_error:
                    app.logger.error(f"生成密碼雜湊錯誤: {str(hash_error)}")
                    return jsonify({'status': 'error', 'message': '密碼處理錯誤'}), 500
                
                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, phone, password, address, birthday)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (username, email, phone, hashed_pw, address, birthday))
                    conn.commit()
                except Exception as db_error:
                    app.logger.error(f"資料庫插入錯誤: {str(db_error)}")
                    return jsonify({'status': 'fail', 'message': '資料庫錯誤，註冊失敗'}), 500
                
                cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
                user = cursor.fetchone()
                
                if not user:
                    app.logger.error("註冊後無法找到用戶記錄")
                    return jsonify({'status': 'error', 'message': '註冊處理錯誤'}), 500
                
                session['user_id'] = user['id']
                session['username'] = username
                
                token = create_access_token(identity=username)
                
                app.logger.info(f"用戶 {username} 註冊成功")
                return jsonify({
                    'status': 'success', 
                    'message': '註冊成功',
                    'token': token,
                    'redirect': '/dashboard'
                }), 200
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"註冊處理異常: {str(e)}")
        return jsonify({'status': 'error', 'message': '伺服器錯誤，請稍後再試'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        app.logger.info("開始處理登入請求")

        if request.is_json:
            app.logger.info("處理JSON格式登入請求")
            data = request.get_json()
        elif request.form:
            app.logger.info("處理表單格式登入請求")
            data = request.form
        else:
            app.logger.warning("未檢測到有效的請求數據")
            return jsonify({'status': 'fail', 'message': '無法解析請求數據'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        app.logger.info(f"用戶 {username} 嘗試登入")

        if not username or not password:
            app.logger.warning("缺少用戶名或密碼")
            return jsonify({'status': 'fail', 'message': '請輸入使用者名稱和密碼'}), 400

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                app.logger.debug(f"用戶查詢結果: {user}")

                if not user:
                    app.logger.warning(f"使用者不存在: {username}")
                    return jsonify({'status': 'fail', 'message': '帳號或密碼錯誤'}), 401
                
                stored_pw = user['password']
                is_valid = False
                
                app.logger.debug(f"存儲的密碼雜湊 (前10位): {stored_pw[:10] if len(stored_pw) > 10 else stored_pw}")
                
                try:
                    pw_bytes = password.encode('utf-8')
                    stored_pw_bytes = stored_pw.encode('utf-8')
                    is_valid = bcrypt.checkpw(pw_bytes, stored_pw_bytes)
                    app.logger.debug(f"Bcrypt驗證結果: {is_valid}")
                except Exception as e:
                    app.logger.error(f"Bcrypt驗證失敗: {str(e)}, 將嘗試純文本比較")
                    is_valid = (stored_pw == password)
                    app.logger.debug(f"純文本比較結果: {is_valid}")
                
                if is_valid:
                    app.logger.info(f"用戶 {username} 登入成功")
                    
                    session['user_id'] = user['id']
                    session['username'] = username
                    
                    token = create_access_token(identity=username)
                    
                    if request.is_json:
                        app.logger.debug("返回JSON登入成功響應")
                        return jsonify({
                            'status': 'success',
                            'message': '登入成功',
                            'token': token,
                            'redirect': '/dashboard'
                        })
                    else:
                        app.logger.debug("重定向到儀表板")
                        return redirect(url_for('dashboard') + f'?token={token}')
                else:
                    app.logger.warning(f"密碼不正確: {username}")
                    return jsonify({'status': 'fail', 'message': '帳號或密碼錯誤'}), 401
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"登入處理異常: {str(e)}")
        return jsonify({'status': 'error', 'message': '伺服器錯誤，請稍後再試'}), 500

# ========= 密碼重置工具 =========
@app.route('/admin/reset-password', methods=['POST'])
def reset_password():
    if not app.debug:
        return jsonify({'status': 'error', 'message': '此功能僅在開發模式可用'}), 403
        
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('password', 'temp123')
    
    if not username:
        return jsonify({'status': 'fail', 'message': '請提供用戶名'}), 400
        
    try:
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET password = %s WHERE username = %s", 
                              (hashed_pw, username))
                conn.commit()
                if cursor.rowcount > 0:
                    return jsonify({
                        'status': 'success', 
                        'message': f'用戶 {username} 密碼已重置',
                        'password': new_password
                    })
                else:
                    return jsonify({'status': 'fail', 'message': '找不到指定用戶'}), 404
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"重置密碼錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': '密碼重置失敗'}), 500

# ========= 查詢點數 =========
@app.route('/api/points', methods=['GET'])
@jwt_required()
def get_points():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT points FROM users WHERE username = %s", (current_user,))
            result = cursor.fetchone()
            if result:
                return jsonify({'points': result['points']})
            else:
                return jsonify({'message': '使用者不存在'}), 404
    finally:
        conn.close()

# ========= 商品列表 =========
@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_products():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, points_required FROM products")
            products = cursor.fetchall()
            return jsonify(products)
    finally:
        conn.close()

# ========= 檢查用戶是否已登入 =========
@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')})
    else:
        return jsonify({'authenticated': False})

# ========= 資料庫初始化 =========
@app.route('/admin/init-db', methods=['GET'])
def init_db():
    if not app.debug:
        return jsonify({'status': 'error', 'message': '此功能僅在開發模式可用'}), 403
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'users'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    address TEXT NOT NULL,
                    birthday DATE NOT NULL,
                    points INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                app.logger.info("創建users表成功")
                
            cursor.execute("SHOW TABLES LIKE 'products'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    points_required INT NOT NULL,
                    description TEXT,
                    image_url VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                app.logger.info("創建products表成功")
                
                cursor.execute("""
                INSERT INTO products (name, points_required, description) VALUES
                ('環保袋', 50, '可重複使用的環保購物袋'),
                ('不鏽鋼吸管', 100, '可重複使用的不鏽鋼吸管套裝'),
                ('有機肥料', 200, '由回收有機垃圾製成的優質肥料')
                """)
                app.logger.info("添加示例產品成功")
            
            conn.commit()
            return jsonify({'status': 'success', 'message': '資料庫初始化成功'})
    except Exception as e:
        app.logger.error(f"資料庫初始化錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': f'資料庫初始化失敗: {str(e)}'}), 500
    finally:
        conn.close()

# ========= 管理員建立帳號功能 =========
@app.route('/create-account-page')
def create_account_page():
    return render_template('create_account.html')

@app.route('/admin/create-account', methods=['POST'])
def admin_create_account():
    try:
        if not request.is_json:
            return jsonify({'status': 'fail', 'message': '請使用JSON格式提交數據'}), 400
            
        data = request.get_json()
        if data is None:
            return jsonify({'status': 'fail', 'message': '無法解析請求數據'}), 400
            
        app.logger.info(f"管理員建立帳號數據: {data}")

        required_fields = ['username', 'email', 'phone', 'password', 'address', 'birthday']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'status': 'fail', 
                'message': f'請提供必要欄位: {", ".join(missing_fields)}'
            }), 400

        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        address = data.get('address')
        birthday = data.get('birthday')
        points = int(data.get('points', 0))

        if not password:
            return jsonify({'status': 'fail', 'message': '密碼不能為空'}), 400

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, email))
                if cursor.fetchone():
                    return jsonify({'status': 'fail', 'message': '使用者名稱或Email已存在'}), 409

                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute("""
                    INSERT INTO users (username, email, phone, password, address, birthday, points)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (username, email, phone, hashed_pw, address, birthday, points))
                conn.commit()
                
                app.logger.info(f"管理員成功建立帳號: {username}")
                return jsonify({
                    'status': 'success', 
                    'message': '帳號建立成功',
                    'account_info': {
                        'username': username,
                        'email': email,
                        'points': points
                    }
                }), 200
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"管理員建立帳號異常: {str(e)}")
        return jsonify({'status': 'error', 'message': '伺服器錯誤，請稍後再試'}), 500

# ========= 審核回收物 =========
@app.route("/review")
def review():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, product_name, points, created_at, status FROM redeem_requests WHERE status='待審核'")
        requests = cursor.fetchall()
        cursor.close()
        return render_template("review.html", requests=requests)
    finally:
        conn.close()

@app.route("/review/submit", methods=["POST"])
def review_submit():
    req_id = request.form.get("id")
    status = request.form.get("status")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE redeem_requests SET status=%s WHERE id=%s", (status, req_id))
        conn.commit()
        cursor.close()
        return redirect(url_for("review"))
    finally:
        conn.close()

@app.route('/admin/test-db', methods=['GET'])
def test_db_connection():
    """測試資料庫連接"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': '資料庫連接成功',
            'database': db_config['database'],
            'host': db_config['host']
        }), 200
    except Exception as e:
        app.logger.error(f"資料庫連接測試失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'資料庫連接失敗: {str(e)}'
        }), 500

@app.route('/admin/db-status', methods=['GET'])
def get_db_status():
    """獲取資料庫狀態和表格信息"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 檢查資料庫是否存在
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            
            # 獲取所有表格
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            table_info = {}
            for table in tables:
                table_name = list(table.values())[0]
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                table_info[table_name] = count
        
        connection.close()
        
        return jsonify({
            'status': 'success',
            'database': current_db,
            'tables': table_info,
            'config': {
                'host': db_config['host'],
                'database': db_config['database'],
                'user': db_config['user']
            }
        }), 200
    except Exception as e:
        app.logger.error(f"獲取資料庫狀態失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'無法獲取資料庫狀態: {str(e)}'
        }), 500

@app.route('/db-management-page')
def db_management_page():
    return render_template('db_management.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
