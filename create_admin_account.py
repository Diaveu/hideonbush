import pymysql
import bcrypt
import sys
import os

# 資料庫配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'eva100422',
    'database': 'eco_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def create_admin_account():
    """創建後台管理員帳號"""
    
    # 管理員帳號資訊
    admin_data = {
        'username': 'admin',
        'email': 'admin@backend.com',
        'phone': '0900000000',
        'password': 'admin123',
        'address': '後台管理系統',
        'birthday': '1990-01-01',
        'points': 9999
    }
    
    try:
        # 連接資料庫
        connection = pymysql.connect(**db_config)
        print(f"✅ 成功連接到資料庫: {db_config['database']}")
        
        with connection.cursor() as cursor:
            # 檢查users表是否存在
            cursor.execute("SHOW TABLES LIKE 'users'")
            if not cursor.fetchone():
                print("📋 創建users表...")
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
                print("✅ users表創建成功")
            
            # 檢查管理員帳號是否已存在
            cursor.execute("SELECT * FROM users WHERE username = %s", (admin_data['username'],))
            existing_admin = cursor.fetchone()
            
            if existing_admin:
                print(f"⚠️  管理員帳號 '{admin_data['username']}' 已存在，更新密碼...")
                # 更新現有管理員的密碼
                hashed_password = bcrypt.hashpw(admin_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute(
                    "UPDATE users SET password = %s, points = %s WHERE username = %s",
                    (hashed_password, admin_data['points'], admin_data['username'])
                )
            else:
                print(f"👤 創建新的管理員帳號: {admin_data['username']}")
                # 加密密碼
                hashed_password = bcrypt.hashpw(admin_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # 插入管理員帳號
                cursor.execute("""
                    INSERT INTO users (username, email, phone, password, address, birthday, points)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    admin_data['username'],
                    admin_data['email'],
                    admin_data['phone'],
                    hashed_password,
                    admin_data['address'],
                    admin_data['birthday'],
                    admin_data['points']
                ))
            
            # 提交變更
            connection.commit()
            
            print("\n🎉 後台管理員帳號創建/更新成功！")
            print("=" * 50)
            print("📋 後台登入資訊:")
            print(f"   使用者名稱: {admin_data['username']}")
            print(f"   密碼: {admin_data['password']}")
            print(f"   Email: {admin_data['email']}")
            print(f"   初始點數: {admin_data['points']}")
            print("=" * 50)
            print("🔗 登入網址: http://localhost:5000/admin_login-page")
            print("🏠 後台管理: http://localhost:5000/backmanament-page")
            print("\n✨ 您現在可以使用這個帳號登入後台系統了！")
            
    except pymysql.Error as e:
        print(f"❌ 資料庫錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()
            print("🔌 資料庫連接已關閉")

if __name__ == "__main__":
    create_admin_account()
