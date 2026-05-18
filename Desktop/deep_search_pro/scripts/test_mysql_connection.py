"""
本地 MySQL 连通性自检（读取项目根目录 .env）。

用法（在项目根目录）:
  python scripts/test_mysql_connection.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import find_dotenv, load_dotenv
from mysql.connector import connect, Error

from tools.mysql_tools import get_db_config, _format_mysql_error


def main() -> int:
    load_dotenv(find_dotenv(usecwd=True))
    try:
        config = get_db_config()
    except ValueError as e:
        print(f"[FAIL] 配置错误: {e}")
        return 1

    safe = {k: v for k, v in config.items() if k != "password"}
    print("[INFO] 连接参数:", safe)

    try:
        with connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES")
                tables = [r[0] for r in cur.fetchall()]
        print("[OK] 连接成功")
        if tables:
            print("[OK] 表:", ", ".join(tables))
        else:
            print("[WARN] 库为空，请执行: mysql -u root -p asset_vuln_db < sql/init_asset_vuln_db.sql")
        return 0
    except Error as e:
        print("[FAIL]", _format_mysql_error(e, config))
        print("\n常见处理:")
        print("  1. 用 MySQL Workbench / 命令行确认 root 真实密码")
        print("  2. 修改 .env 中 MYSQL_PASSWORD=你的真实密码")
        print("  3. 创建库并导入: sql/init_asset_vuln_db.sql")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
