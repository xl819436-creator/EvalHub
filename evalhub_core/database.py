import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "evalhub.db"

DatabasePath = Union[str, Path]


def get_connection(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> sqlite3.Connection:
    """
    创建SQLite数据库连接。

    SQLite默认不一定启用外键约束，
    因此每次连接后都主动执行PRAGMA foreign_keys = ON。
    """
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """
    初始化EvalHub数据库。

    Day 10先创建三张核心表：
    1. datasets
    2. evaluation_jobs
    3. evaluation_runs
    """
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                version TEXT NOT NULL DEFAULT 'v1.0',
                file_path TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                total_cases INTEGER NOT NULL DEFAULT 0
                    CHECK (total_cases >= 0),
                completed_cases INTEGER NOT NULL DEFAULT 0
                    CHECK (
                        completed_cases >= 0
                        AND completed_cases <= total_cases
                    ),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (dataset_id)
                    REFERENCES datasets(id)
                    ON DELETE RESTRICT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                case_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                expected_output TEXT,
                actual_output TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                latency_ms REAL CHECK (
                    latency_ms IS NULL OR latency_ms >= 0
                ),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (job_id)
                    REFERENCES evaluation_jobs(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_dataset(
    name: str,
    description: str = "",
    version: str = "v1.0",
    file_path: Optional[str] = None,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> int:
    """插入一条数据集记录，并返回数据集ID。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO datasets (
                name,
                description,
                version,
                file_path
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                description,
                version,
                file_path,
            ),
        )

        connection.commit()

        dataset_id = cursor.lastrowid

        if dataset_id is None:
            raise RuntimeError("数据集插入成功，但没有获得ID。")

        return int(dataset_id)

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_dataset(
    dataset_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> Optional[Dict[str, Any]]:
    """根据ID查询一条数据集记录。"""
    connection = get_connection(database_path)

    try:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                description,
                version,
                file_path,
                created_at
            FROM datasets
            WHERE id = ?
            """,
            (dataset_id,),
        ).fetchone()

        return dict(row) if row is not None else None

    finally:
        connection.close()


def update_dataset(
    dataset_id: int,
    name: str,
    description: str,
    version: str,
    file_path: Optional[str],
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """完整更新一条数据集记录。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.execute(
            """
            UPDATE datasets
            SET
                name = ?,
                description = ?,
                version = ?,
                file_path = ?
            WHERE id = ?
            """,
            (name, description, version, file_path, dataset_id),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到dataset_id={dataset_id}的数据集。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_dataset(
    dataset_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """删除没有被评测任务引用的数据集。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.execute(
            "DELETE FROM datasets WHERE id = ?",
            (dataset_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到dataset_id={dataset_id}的数据集。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def create_evaluation_job(
    dataset_id: int,
    name: str,
    provider_name: str,
    total_cases: int,
    status: str = "pending",
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> int:
    """创建评测任务，并返回任务ID。"""
    if total_cases < 0:
        raise ValueError("total_cases不能小于0。")

    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO evaluation_jobs (
                dataset_id,
                name,
                provider_name,
                status,
                total_cases,
                completed_cases
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                name,
                provider_name,
                status,
                total_cases,
                0,
            ),
        )

        connection.commit()

        job_id = cursor.lastrowid

        if job_id is None:
            raise RuntimeError("评测任务插入成功，但没有获得ID。")

        return int(job_id)

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def create_evaluation_run(
    job_id: int,
    case_name: str,
    prompt: str,
    expected_output: Optional[str] = None,
    actual_output: Optional[str] = None,
    status: str = "pending",
    latency_ms: Optional[float] = None,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> int:
    """给某个评测任务插入一条运行记录。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO evaluation_runs (
                job_id,
                case_name,
                prompt,
                expected_output,
                actual_output,
                status,
                latency_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                case_name,
                prompt,
                expected_output,
                actual_output,
                status,
                latency_ms,
            ),
        )

        connection.commit()

        run_id = cursor.lastrowid

        if run_id is None:
            raise RuntimeError("运行记录插入成功，但没有获得ID。")

        return int(run_id)

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_job(
    job_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> Optional[Dict[str, Any]]:
    """根据ID查询一条评测任务。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                dataset_id,
                name,
                provider_name,
                status,
                total_cases,
                completed_cases,
                created_at,
                updated_at
            FROM evaluation_jobs
            WHERE id = ?
            """,
            (job_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def update_evaluation_job(
    job_id: int,
    name: str,
    provider_name: str,
    status: str,
    total_cases: int,
    completed_cases: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """完整更新一条评测任务记录。"""
    if total_cases < 0:
        raise ValueError("total_cases不能小于0。")

    if completed_cases < 0 or completed_cases > total_cases:
        raise ValueError(
            "completed_cases必须在0和total_cases之间。"
        )

    connection = get_connection(database_path)

    try:
        cursor = connection.execute(
            """
            UPDATE evaluation_jobs
            SET
                name = ?,
                provider_name = ?,
                status = ?,
                total_cases = ?,
                completed_cases = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                name,
                provider_name,
                status,
                total_cases,
                completed_cases,
                job_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到job_id={job_id}的评测任务。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_evaluation_job(
    job_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """删除评测任务；关联的run由外键级联删除。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.execute(
            "DELETE FROM evaluation_jobs WHERE id = ?",
            (job_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到job_id={job_id}的评测任务。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def get_runs_by_job(
    job_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> List[Dict[str, Any]]:
    """查询一个job对应的全部run记录。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                job_id,
                case_name,
                prompt,
                expected_output,
                actual_output,
                status,
                latency_ms,
                created_at
            FROM evaluation_runs
            WHERE job_id = ?
            ORDER BY id
            """,
            (job_id,),
        )

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_evaluation_run(
    run_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> Optional[Dict[str, Any]]:
    """根据ID查询一条运行记录。"""
    connection = get_connection(database_path)

    try:
        row = connection.execute(
            """
            SELECT
                id,
                job_id,
                case_name,
                prompt,
                expected_output,
                actual_output,
                status,
                latency_ms,
                created_at
            FROM evaluation_runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()

        return dict(row) if row is not None else None

    finally:
        connection.close()


def update_evaluation_run(
    run_id: int,
    case_name: str,
    prompt: str,
    expected_output: Optional[str],
    actual_output: Optional[str],
    status: str,
    latency_ms: Optional[float],
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """完整更新一条运行记录。"""
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("latency_ms不能小于0。")

    connection = get_connection(database_path)

    try:
        cursor = connection.execute(
            """
            UPDATE evaluation_runs
            SET
                case_name = ?,
                prompt = ?,
                expected_output = ?,
                actual_output = ?,
                status = ?,
                latency_ms = ?
            WHERE id = ?
            """,
            (
                case_name,
                prompt,
                expected_output,
                actual_output,
                status,
                latency_ms,
                run_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到run_id={run_id}的运行记录。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_evaluation_run(
    run_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """删除一条运行记录。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.execute(
            "DELETE FROM evaluation_runs WHERE id = ?",
            (run_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到run_id={run_id}的运行记录。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def update_job_progress(
    job_id: int,
    completed_cases: int,
    status: str = "running",
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """更新评测任务进度和任务状态。"""
    connection = get_connection(database_path)

    try:
        job_row = connection.execute(
            "SELECT total_cases FROM evaluation_jobs WHERE id = ?",
            (job_id,),
        ).fetchone()

        if job_row is None:
            raise ValueError(f"没有找到job_id={job_id}的评测任务。")

        if completed_cases < 0 or completed_cases > job_row["total_cases"]:
            raise ValueError(
                "completed_cases必须在0和total_cases之间。"
            )

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE evaluation_jobs
            SET
                completed_cases = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                completed_cases,
                status,
                job_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"没有找到job_id={job_id}的评测任务。")

        connection.commit()

    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise

    finally:
        connection.close()


def list_table_names(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> List[str]:
    """查询当前数据库中已经创建的数据表。"""
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        return [row["name"] for row in cursor.fetchall()]

    finally:
        connection.close()


def main() -> None:
    """直接运行本文件时，初始化正式数据库。"""
    init_database()

    print("EvalHub数据库初始化成功。")
    print(f"数据库位置：{DEFAULT_DATABASE_PATH}")
    print("已创建的数据表：")

    for table_name in list_table_names():
        print(f"- {table_name}")


if __name__ == "__main__":
    main()
