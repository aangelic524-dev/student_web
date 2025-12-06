import requests
import os

# 创建会话以便保持登录状态
session = requests.Session()

# 先登录
def login(session):
    login_url = 'http://127.0.0.1:5000/auth/login'
    
    # 先获取登录页面
    response = session.get(login_url)
    if response.status_code != 200:
        return False
    
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'submit': '登录'
    }
    
    # 发送登录请求
    response = session.post(login_url, data=login_data, allow_redirects=True)
    
    # 检查是否登录成功
    return response.status_code == 200 and '未登录' not in response.text

# 测试导入学生数据
def test_import_students(session):
    url = 'http://127.0.0.1:5000/bulk/import'
    
    # 准备文件
    file_path = 'test_grades.csv'
    
    # 准备表单数据
    data = {
        'file_type': 'csv',
        'data_type': 'students',
        'skip_duplicates': 'off'
    }
    
    # 发送请求
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = session.post(url, data=data, files=files)
    
    # 打印结果
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

# 测试导入成绩数据
def test_import_grades(session):
    url = 'http://127.0.0.1:5000/bulk/import'
    
    # 准备文件
    file_path = 'test_grades.csv'
    
    # 准备表单数据
    data = {
        'file_type': 'csv',
        'data_type': 'grades',
        'skip_duplicates': 'off'
    }
    
    # 发送请求
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = session.post(url, data=data, files=files)
    
    # 打印结果
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

# 执行测试
if login(session):
    print("登录成功！")
    print("\n测试导入学生数据...")
    test_import_students(session)
    print("\n测试导入成绩数据...")
    test_import_grades(session)
else:
    print("登录失败！")
