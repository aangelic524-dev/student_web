import requests
import os

# 创建测试CSV文件内容
csv_content = '''学号,姓名,性别,年级,院系,班级,专业,入学日期
JW250101,苏琪彤（最终更新）,女,25,计算机与网络学院,计算机网络技术1班,计算机网络技术,2025-12-06
JW250104,王小明,男,25,计算机与网络学院,计算机科学与技术1班,计算机科学与技术,2025-12-06
''' 

# 保存测试CSV文件
test_csv_path = 'test_final.csv'
with open(test_csv_path, 'w', encoding='utf-8') as f:
    f.write(csv_content)

try:
    # 创建会话
    session = requests.Session()
    
    # 1. 登录
    login_url = 'http://localhost:5000/auth/login'
    
    # 获取登录页面，提取CSRF令牌
    login_page = session.get(login_url)
    import re
    
    # 从登录页面中提取CSRF令牌
    csrf_token = ''
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', login_page.text)
    if match:
        csrf_token = match.group(1)
        print('获取到CSRF令牌:', csrf_token)
    else:
        print('未找到CSRF令牌')
    
    # 准备登录数据，包含CSRF令牌
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    # 发送登录请求
    login_response = session.post(login_url, data=login_data, allow_redirects=True)
    
    # 调试信息
    print('登录响应状态码:', login_response.status_code)
    print('登录响应URL:', login_response.url)
    print('登录响应头:', dict(login_response.headers))
    
    # 检查登录是否成功 - 简单检查是否重定向到dashboard
    if 'dashboard' in login_response.url:
        print('登录成功！')
    elif login_response.status_code == 200 and '用户名或密码错误' not in login_response.text:
        # 如果返回200且不包含错误信息，也认为登录成功
        print('登录成功！（基于响应状态和内容判断）')
    else:
        print('登录失败！')
        print('登录响应中是否包含错误信息:', '用户名或密码错误' in login_response.text)
        # print('登录响应内容:', login_response.text)
        exit(1)
    
    # 2. 测试批量导入功能
    import_url = 'http://localhost:5000/bulk/import'
    
    # 准备表单数据
    form_data = {
        'file_type': 'csv',
        'data_type': 'students',
        'skip_duplicates': 'off'  # 使用off来更新重复记录
    }
    
    # 准备文件数据
    files = {
        'file': open(test_csv_path, 'rb')
    }
    
    # 发送批量导入请求
    import_response = session.post(import_url, data=form_data, files=files)
    
    # 检查导入结果
    print('\n批量导入响应状态码:', import_response.status_code)
    print('批量导入响应URL:', import_response.url)
    
    if import_response.status_code == 200:
        # 显示响应内容的前1000个字符
        print('批量导入响应内容:', import_response.text[:1000])
        
        # 检查响应内容
        if '导入成功' in import_response.text or '成功' in import_response.text:
            print('批量导入成功！')
        elif '唯一约束失败' in import_response.text or 'IntegrityError' in import_response.text:
            print('批量导入失败：唯一约束失败')
        elif '请选择文件' in import_response.text:
            print('批量导入失败：未检测到文件')
        else:
            print('批量导入响应内容中未找到明确的成功或失败消息')
    else:
        print('批量导入请求失败')
        print('响应内容:', import_response.text[:500])
    
    # 3. 测试查询功能，验证导入结果
    query_url = 'http://localhost:5000/query'
    query_response = session.get(query_url)
    
    if query_response.status_code == 200:
        # 检查测试学生是否在响应中
        if 'JW250101' in query_response.text and 'JW250104' in query_response.text:
            print('\n查询验证成功：所有测试学生ID都在查询页面中')
        else:
            print('\n查询验证失败：测试学生ID不在查询页面中')
    else:
        print('\n查询请求失败')
        # print('查询响应内容:', query_response.text)
    
    # 4. 登出
    logout_url = 'http://localhost:5000/auth/logout'
    logout_response = session.get(logout_url)
    print('\n登出成功！')
    
except Exception as e:
    print(f'测试过程中出错: {e}')
finally:
    # 关闭文件
    if 'files' in locals() and 'file' in files:
        files['file'].close()
    
    # 删除测试CSV文件
    if os.path.exists(test_csv_path):
        os.remove(test_csv_path)
        print('\n测试CSV文件已删除')
