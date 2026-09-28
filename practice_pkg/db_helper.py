import pymysql

# MySQL connection configuration
DB_CONFIG = dict(
    host="172.29.192.1",
    user="root",
    password="tyston124",  # MySQL password
    database="rosdb",      # Schema name
    charset="utf8mb4"
)


class DB:
    def __init__(self, **config):
        self.config = config
        self.init_db()

    def connect(self):
        """Establish MySQL database connection"""
        return pymysql.connect(**self.config)

    def init_db(self):
        """
        Automatically create the turtlepos table
        - seq: Unique auto-increment primary key
        - id: Session/round ID (1, 2, 3...)
        - time: DB insertion timestamp
        """
        sql = """
        CREATE TABLE IF NOT EXISTS turtlepos (
            seq INT AUTO_INCREMENT PRIMARY KEY,
            id INT NOT NULL,
            x FLOAT NOT NULL,
            y FLOAT NOT NULL,
            theta FLOAT NOT NULL,
            time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
        except Exception as e:
            print(f"[DB Error] Failed to initialize table: {e}")

    def get_max_session_id(self) -> int:
        """Fetch the latest session ID (MAX(id)) stored in the database"""
        sql = "SELECT IFNULL(MAX(id), 0) FROM turtlepos"
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            print(f"[DB Error] Failed to fetch max session ID: {e}")
            return 0

    def insert_poses(self, pose_list: list) -> bool:
        """
        Batch insert accumulated pose data into the database
        pose_list format: [(id, x1, y1, theta1), (id, x2, y2, theta2), ...]
        """
        if not pose_list:
            return True

        sql = "INSERT INTO turtlepos (id, x, y, theta) VALUES (%s, %s, %s, %s)"
        with self.connect() as conn:
            try:
                with conn.cursor() as cur:
                    cur.executemany(sql, pose_list)
                conn.commit()
                return True
            except Exception as e:
                print(f"[DB Error] Failed to batch insert pose data: {e}")
                conn.rollback()
                return False