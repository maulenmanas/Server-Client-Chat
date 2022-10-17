import json
import asyncio
# import psycopg2 as pg
import sqlite3 as sql
import datetime
import hashlib
import bcrypt


class ChatServer:

    def __init__(self, server_name, ip, port, loop):
        self.server_name = server_name
        self.connections = {}
        self.conn, self.cursor = self.init_db()
        self.server = loop.run_until_complete(
            asyncio.start_server(
                self.accept_connection, ip, port))

    def db_register(self, *record):
        print(record)
        self.cursor.execute("insert into users(username, hashpass, lastseen) values(?,?,?)", record)
        self.conn.commit()

    def db_message(self, *record):
        print(record)
        self.cursor.execute("insert into history(sender, message, date, receiver) values(?,?,?,?)", record)
        self.conn.commit()

    def exist(self, username):
        self.cursor.execute("select * from users where username = ?", (username,))
        return self.cursor.fetchone()
    def db_change_pw(self, *record):
        print(record)
        self.cursor.execute("update users set hashpass = ? where username = ?", record)
        self.conn.commit()
    def db_update_date(self, *record):
        self.cursor.execute("update users set lastseen = ? where username = ?", record)
        self.conn.commit()
    def db_get_history(self, user):
        rec = self.exist(user)
        print(rec)
        self.cursor.execute("select * from history where date > ? and (receiver = ? or receiver is null) \
        order by date asc", (rec[2], rec[0],))
        return self.cursor.fetchall()
    def init_db(self):
        try:
            con = sql.connect("manas.db")
            cursor = con.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS users(username, hashpass, lastseen)")
            cursor.execute("CREATE TABLE IF NOT EXISTS history(sender, message, date, receiver)")
            return (con, cursor)
        except:
            print(f'Error connecting to Database')

    async def broadcast(self, message):
        print(message)
        self.connections = {x: y for (x, y) in self.connections.items() if not y.is_closing()}
        for writer in self.connections.values():
            try:
                writer.write((message + "\n").encode("utf-8"))
                await writer.drain()
            except:
                pass
    async def handle_connection(self, reader, writer):
        data = (await reader.read(100)).decode("utf-8")
        print(data)
        if not data:
            return False
        data = json.loads(data)
        if data[0] == 'chat':
            user = data[1]
            self.connections[user] = writer
            log = self.db_get_history(user)
            writer.write(json.dumps(log).encode())
            await writer.drain()
        if data[0] == 'q':
            user = data[1]
            del self.connections[user]
            self.db_change_date(datetime.datetime.now().strftime("%H:%M:%S"), user)
            writer.close()
        if data[0] == 'c':
            #print(type(data[0]), type(data[1]))
            self.db_change_pw(await self.hash_password(data[2]), data[1])
        if data[0] == 'p':
            user = data[1]
            message = data[2]
            receiver = data[3]
            self.db_message(user, message, datetime.datetime.now().strftime("%H:%M:%S"), receiver)
            if self.connections.get(receiver) is not None:
                if not self.connections[receiver].is_closing():
                    self.connections[receiver].write("private_{}>{}".format(user, message).encode())
        if data[0] == 'm':
            user = data[1]
            message = data[2]
            self.db_message(user, message, datetime.datetime.now().strftime("%H:%M:%S"), None)
            await self.broadcast(user + "> " + message)
        if data[0] == 'r':
            print(data[1:])
            #lst = json.loads(data[2:])
            data[2] = await self.hash_password(data[2])
            self.db_register(data[1], data[2], datetime.datetime.now().strftime("%H:%M:%S"))
        if data[0] == 'e':
            print(data[1])
            rec = self.exist(data[1])
            if rec is None:
                writer.write(json.dumps(False).encode())
            else:
                writer.write(json.dumps(True).encode())
        if data[0] == 'l':
            user = data[1]
            password = data[2]
            rec = self.exist(user)
            if await self.check_passwords(rec[1], password):
                writer.write(json.dumps(True).encode())
                await writer.drain()
            else:
                writer.write(json.dumps(False).encode())
                await writer.drain()
        return True

    async def accept_connection(self, reader, writer):
        print("kek")

        while await self.handle_connection(reader, writer):
            continue

    async def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async def check_passwords(self, hashed, strpass):
        return bcrypt.checkpw(strpass.encode('utf-8'), hashed.encode('utf-8'))


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
server = ChatServer("Test server", "127.0.0.1", 8888, loop)

# Serve requests until Ctrl+C is pressed
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.conn.close()
loop.close()
