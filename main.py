import ssl
from aiohttp import web
from datetime import datetime
import sqlite3
import json
import logging

# 配置 logging 模块，添加时间戳
logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')

def db_init(db_name):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # 创建表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        create_time TEXT,
        sn TEXT,
        sku TEXT,
        version TEXT,
        build_time TEXT,
        ai_sdk_version TEXT,
        firmware TEXT,
        update_times INTEGER,
        update_time TEXT,
        local_ip TEXT,
        outer_ip TEXT
    )
    ''')
    # 提交事务
    conn.commit()
    # 关闭连接
    conn.close()

def de_insert(data, outer_ip):
    if 'sn' in data:
        sn = data['sn']
    else:
        sn = ""

    if 'sku' in data:
        sku = data['sku']
    else:
        sku = ""

    if 'version' in data:
        version = data['version']
    else:
        version = ""

    if 'buildtime' in data:
        build_time = data['buildtime']
    else:
        build_time = ""

    if 'ai_sdk_version' in data:
        ai_sdk_version = data['ai_sdk_version']
    else:
        ai_sdk_version = ""

    if 'firmware' in data:
        firmware = data['firmware']
    else:
        firmware = ""

    if 'ip' in data:
        local_ip = data['ip']
    else:
        local_ip = ""

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    conn = sqlite3.connect('iot_device.db')
    cursor = conn.cursor()
    cursor.execute('SELECT update_times FROM devices WHERE sn = ?', (sn,))
    rows = cursor.fetchone()
    if rows:
        update_times = rows[0] + 1
        cursor.execute('''
        UPDATE devices SET sku = ?, version = ?, build_time = ?, ai_sdk_version = ?, firmware = ?, update_times = ?, update_time = ?, local_ip = ?, outer_ip = ? WHERE sn = ?
        ''', (sku, version, build_time, ai_sdk_version, firmware, update_times, current_time, local_ip, outer_ip, sn))
    else:
        cursor.execute('''
        INSERT INTO devices (create_time, sn, sku, version, build_time, ai_sdk_version, firmware, update_times, local_ip, outer_ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_time, sn, sku, version, build_time, ai_sdk_version, firmware, 0, local_ip, outer_ip))
    conn.commit()
    conn.close()


async def handle_get(request):
    return web.Response(text = "Hello, this is a GET request!\n")


async def handle_post(request):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.Response(text = "Invalid JSON data", status = 400)

    if 'sn' not in data:
        return web.Response(text = "Invalid JSON data no sn", status = 400)

    de_insert(data, request.remote)

    post_data = await request.text()
    logging.debug(post_data)
    response_data = {
        "code": 0,
        "message": "success"
    }
    return web.json_response(response_data, status = 200)


if __name__ == '__main__':

    db_init('iot_device.db')

    app = web.Application()
    app.router.add_get('/', handle_get)
    app.router.add_post('/', handle_post)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile = 'server.pem')

    web.run_app(app, host='0.0.0.0', port = 10443, ssl_context = ssl_context)
