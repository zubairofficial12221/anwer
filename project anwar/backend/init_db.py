import os
from pathlib import Path

from dotenv import load_dotenv
import mysql.connector


def main() -> None:
    load_dotenv()

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")

    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        autocommit=False,
    )
    try:
        cur = conn.cursor()
        for _ in cur.execute(sql, multi=True):
            pass
        conn.commit()
        print("OK: database schema applied from schema.sql")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

