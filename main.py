import psycopg2


def create_db(conn):
    with conn.cursor() as cur:
        cur.execute('''
        CREATE TABLE IF NOT EXISTS clients(
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(40),
            last_name VARCHAR(40),
            email VARCHAR(40)
        );
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS phones(
            id SERIAL PRIMARY KEY,
            phone VARCHAR(40),
            client_id INTEGER REFERENCES clients(id)
        );
        ''')
        conn.commit()


def add_client(conn, first_name, last_name, email, phones=tuple()):
    with conn.cursor() as cur:
        cur.execute('''
        INSERT INTO clients(first_name, last_name, email) VALUES(%s, %s, %s) RETURNING id;
        ''', (first_name, last_name, email))
        client_id = cur.fetchone()[0]
        for phone in phones:
            cur.execute('''
            INSERT INTO phones(phone, client_id) VALUES(%s, %s);
            ''', (phone, client_id))
        conn.commit()


def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute('''
        INSERT INTO phones(phone, client_id) VALUES(%s, %s);
            ''', (phone, client_id))
        conn.commit()


def change_client(conn, client_id, *, first_name=None, last_name=None, email=None, phones=tuple()):
    with conn.cursor() as cur:
        if first_name:
            cur.execute('''
                UPDATE clients SET first_name=%s WHERE id=%s;
            ''', (first_name, client_id))
        if last_name:
            cur.execute('''
                UPDATE clients SET last_name=%s WHERE id=%s;
            ''', (last_name, client_id))
        if email:
            cur.execute('''
                UPDATE clients SET email=%s WHERE id=%s;
            ''', (email, client_id))
        if phones:
            # Обновить список телефонов - удалить старый список и добавить новый
            cur.execute('''
                DELETE FROM phones WHERE client_id=%s;
            ''', (client_id,))
            for phone in phones:
                add_phone(conn, client_id, phone)
        conn.commit()


def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute('''
            DELETE FROM phones WHERE client_id=%s AND phone=%s;
        ''', (client_id, phone))
        conn.commit()


def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute('''
            DELETE FROM clients WHERE id=%s;
        ''', (client_id,))
        cur.execute('''
            DELETE FROM phones WHERE client_id=%s;
        ''', (client_id,))
        conn.commit()


def find_client(conn, *, first_name='', last_name='', email='', phone=''):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT DISTINCT c.id FROM clients c
            LEFT JOIN phones p ON c.id=p.client_id
            WHERE c.first_name LIKE %s AND c.last_name LIKE %s AND c.email LIKE %s AND p.phone LIKE %s;
        ''', tuple(map(lambda x: f"%{x}%", (first_name, last_name, email, phone))))
        client_id = cur.fetchone()[0]
        cur.execute('''
            SELECT * FROM clients
            WHERE id=%s;
        ''', (client_id,))
        ans = dict(zip(("client_id", "first_name", "last_name", "email"), (cur.fetchone())))
        cur.execute('''
            SELECT phone FROM phones
            WHERE client_id=%s;
        ''', (client_id,))
        ans["phones"] = sum(map(lambda x: list(x), cur.fetchall()), [])
        return ans


if __name__ == "__main__":
    with psycopg2.connect(database="clients_db", user="postgres", password="1234") as conn:
        create_db(conn)
        add_client(conn, "Maxim", "Lazariuc", "lazariucmaxim@test.com", ("+1234", "+4321"))
        add_phone(conn, 1, "+12345678")
        change_client(conn, 1, first_name="Max", email="maxlazariuc@testing.com", phones=("+987654321", "+000000"))
        delete_phone(conn, 1, "+000000")
        print(find_client(conn, last_name="Lazariuc", phone="+987654321"))
    conn.close()
