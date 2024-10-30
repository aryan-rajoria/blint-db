import datetime
import os
import sqlite3
from contextlib import closing
from pathlib import PurePath

from symbols_db import BLINTDB_LOCATION, DEBUG_MODE, SQLITE_TIMEOUT


# def get_cursor():
#     connection = sqlite3.connect(BLINTDB_LOCATION, timeout=180.0)
#     c = connection.cursor()
#     return connection, c


def create_database():
    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            projects_table = c.execute(
                """
                CREATE TABLE IF NOT EXISTS Projects (
                    pid     INTEGER PRIMARY KEY AUTOINCREMENT,
                    pname   VARCHAR(255),
                    purl    VARCHAR(255) UNIQUE,
                    cbom    BLOB
                );
                """
            )

            binaries_table = c.execute(
                """
                CREATE TABLE IF NOT EXISTS Binaries (
                    bid     INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid     INTEGER,
                    bname   VARCHAR(500),
                    bbom    BLOB,
                            
                    FOREIGN KEY (pid) REFERENCES Projects(pid)
                );
                """
            )

            exports_table = c.execute(
                """
                CREATE TABLE IF NOT EXISTS Exports (
                    infunc  VARCHAR(255) PRIMARY KEY
                );
                """
            )

            binary_exports_table = c.execute(
                """
                CREATE TABLE IF NOT EXISTS BinariesExports (
                    bid INTEGER,
                    eid INTEGER,
                    PRIMARY KEY (bid, eid),
                    FOREIGN KEY (bid) REFERENCES Binaries(bid),
                    FOREIGN KEY (eid) REFERENCES Exports(eid)
                );
                """
            )

            index_table = c.execute(
                """
                CREATE INDEX IF NOT EXISTS export_name_index ON Exports (infunc);
                """
            )
            
            pragma_sync = c.execute("PRAGMA synchronous = 'OFF';")
            pragma_jm = c.execute("PRAGMA journal_mode = 'WAL';")
            pragma_ts = c.execute("PRAGMA temp_store = 'MEMORY';")
            connection.commit()
            if DEBUG_MODE:
                print(
                    projects_table,
                    binaries_table,
                    exports_table,
                    binary_exports_table,
                    index_table,
                    pragma_jm,
                    pragma_sync,
                    pragma_ts,
                )
        connection.commit()


def clear_sqlite_database():
    os.remove(BLINTDB_LOCATION)


def store_sbom_in_sqlite(purl, sbom):
    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute(
                "INSERT INTO blintsboms VALUES (?, ?, jsonb(?))",
                (purl, datetime.datetime.now(), sbom),
            )
        connection.commit()


# add project
def add_projects(project_name, purl=None, cbom=None):
    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute(
                "INSERT INTO Projects (pname, purl, cbom) VALUES (?, ?, ?)",
                (project_name, purl, cbom),
            )
        connection.commit()

    # retrieve pid
    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute("SELECT pid FROM Projects WHERE pname=?", (project_name,))
            res = c.fetchall()

    return res[0][0]


# add binary
def add_binary(binary_file_path, project_id, blint_bom=None, split_word="subprojects/"):
    if isinstance(binary_file_path, PurePath):
        binary_file_path = str(binary_file_path)

    # truncate the binary file path
    binary_file_path = binary_file_path.split(split_word)[1]

    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute(
                "INSERT INTO Binaries (pid, bname, bbom) VALUES (?, ?, ?)",
                (project_id, binary_file_path, blint_bom),
            )
        connection.commit()

    # retrieve bid

    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute("SELECT bid FROM Binaries WHERE bname=?", (binary_file_path,))
            res = c.fetchall()
        connection.commit()

    return res[0][0]


# add export
def add_binary_export(infunc, bid):

    def _fetch_bin_exists(bid, eid):
        with closing(
            sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
        ) as connection:
            with closing(connection.cursor()) as c:
                c.execute(
                    "SELECT bid FROM BinariesExports WHERE bid=? and eid=?", (bid, eid)
                )
                res = c.fetchall()
            connection.commit()
        if res:
            res = res[0][0]
            return res == bid

    def _fetch_infunc_row(infunc):
        with closing(
            sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
        ) as connection:
            with closing(connection.cursor()) as c:
                c.execute("SELECT rowid FROM Exports WHERE infunc=?", (infunc,))
                res = c.fetchall()
            connection.commit()
        return res

    pre_existing = _fetch_infunc_row(infunc)
    if pre_existing:
        eid = pre_existing[0][0]
        if not _fetch_bin_exists(bid, eid):
            with closing(
                sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
            ) as connection:
                with closing(connection.cursor()) as c:
                    c.execute(
                        "INSERT INTO BinariesExports (bid, eid) VALUES (?, ?)",
                        (bid, eid),
                    )
                connection.commit()

        return 0

    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute("INSERT INTO Exports (infunc) VALUES (?)", (infunc,))
        connection.commit()

    eid = _fetch_infunc_row(infunc)[0][0]

    with closing(
        sqlite3.connect(BLINTDB_LOCATION, timeout=SQLITE_TIMEOUT)
    ) as connection:
        with closing(connection.cursor()) as c:
            c.execute(
                "INSERT INTO BinariesExports (bid, eid) VALUES (?, ?)", (bid, eid)
            )
        connection.commit()
