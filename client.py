
# https://asyncio.readthedocs.io/en/latest/tcp_echo.html
import asyncio
from aioconsole import ainput
import json

class Auth():
    def __init__(self, server_ip: str, server_port: int, loop: asyncio.AbstractEventLoop):
        self.__server_ip: str = server_ip
        self.__server_port: int = server_port
        self.__username = "guest"
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__reader: asyncio.StreamReader = None
        self.__writer: asyncio.StreamWriter = None
    @property
    def username(self):
        return self.__username
    @username.setter
    def username(self, username):
        self.__username = username
    @property
    def server_ip(self):
        return self.__server_ip

    @property
    def server_port(self):
        return self.__server_port

    @property
    def loop(self):
        return self.__loop

    @property
    def reader(self):
        return self.__reader

    @property
    def writer(self):
        return self.__writer
    async def chat(self):
        await self.send(["chat", self.username])
        rec = await self.get()
        #print(rec)
        for x in rec:
            #print(x)
            if x[3] is not None:
                print("Private message from {}: {} at {}".format(x[0], x[1], x[2]))
            else :
                print("Common message from {}: {} at {}".format(x[0], x[1], x[2]))
        await asyncio.gather(
                self.receive_messages(),
                self.start_client_cli()
            )
    async def receive_messages(self):
        '''
        Asynchronously receives incoming messages from the
        server.
        '''
        server_message: str = None
        while server_message != 'quit':
            server_message = await self.get()
            print(f"{server_message}")

        if self.loop.is_running():
            self.loop.stop()

    async def get(self):
        '''
        Awaits for messages to be received from self.
        If message is received, returns result as utf8 decoded string
        '''
        res = await self.reader.read(2048)
        #res.decode('utf8')
        #print(res)
        try:
            res = json.loads(res)
        except:
            pass
        return res

    async def start_client_cli(self):
        '''
        Starts the client's command line interface for the user.
        Accepts and forwards user input to the connected server.
        '''
        client_message: str = None
        while client_message != 'quit':
            client_message = (await ainput("")).strip()
            if client_message == "private":
                user = (await ainput("Enter receiver username: ")).strip()
                #while not await self.exist(user):
                 #   print("This user doesn't not exist, Try one more time: ")
                  #  user = (await ainput("")).strip()
                message = (await ainput("")).strip()
                await self.send(["p", self.username, message, user])
            else:
                await self.send(["m", self.username, client_message])

        if self.loop.is_running():
            self.loop.stop()
    async def send(self, message):
        self.writer.write(json.dumps(message).encode('utf8'))
        await self.writer.drain()
    async def register(self):
        #input data
        username = (await ainput("Please enter your username: ")).strip()
        while await self.exist(username):
            username = (await ainput("This username is already taken, Please enter your username: ")).strip()
        password = (await ainput("Please enter your password: ")).strip()
        confirm = (await ainput("Please confirm your password: ")).strip()
        while password != confirm :
            password = await ainput("Your passwords are not the same. Please re-enter password: ")
            confirm = await ainput("Please confirm your password: ")

        await self.send(["r", username, password])

    async def exist(self, username):
        await self.send(["e", username])
        return await self.get()
    
    async def login(self):
        #login by username, ask to register new one
        username = (await ainput("Please enter your username: ")).strip()
        tries = 0
        while await self.exist(username) == False: 
            tries += 1
            print("There is no user with this username")
            if tries >= 3:
                print("Are you sure you created account before? Do you want to register?")
                print("Choose:\n 0 - try to login\nAny other integer - register")
                x = 0
                while True:
                    try:
                        x = int((await ainput()).strip())
                    except ValueError:
                        print("Please input an integer")
                        continue
                    break
                if x:
                    await self.register()
            username = (await ainput("Please enter your username: ")).strip()
        #Check for password validation, limit for tries count
        password = (await ainput("Please enter your password: ")).strip()
        tries = 4
        while await self.check(username, password) == False and tries > 0:
            password = (await ainput("Password is wrong, {} tries left: ".format(tries))).strip()
            tries -= 1
        if await self.check(username, password) == False:
            print("You can no longer enter a password: ")
            return "guest"
        print("You've logged in successfully")
        print("Welcome back {}".format(username))
        return username

    async def check(self, username, password):
        message = ["l", username, password]
        await self.send(message)
        return await self.get()

    async def change_password(self):
        new_password = await ainput("Please enter new password: ")
        confirm = await ainput("Please confirm your password : ")
        while new_password != confirm:
            new_password = await ainput("Your passwords are not the same. Please re-enter password")
            confirm = await ainput("Please confirm your password : ")
        await self.send(["c", self.username, new_password])
    async def run(self):
        self.__reader, self.__writer = await asyncio.open_connection(self.server_ip, self.server_port)
    
        while True:
            #Option menu, interact with command line
            #different scenarios for guest and registered user       
            print("Select an option:")
            print("0. Quit")
            if self.username == 'guest': #for guest
                print("1. Register")
                print("2. Login")
                try:
                    choice = int(input())
                except ValueError:
                    print("Input is wrong, Please input an integer")
                    continue
                if choice == 1:
                    await auth.register()
                elif choice == 2:
                    self.username = await auth.login()
                elif choice == 0:
                    break
                else :
                    print("Input correct option")

            else : #for registered user
                print("1. Change password")
                print("2. Logout")
                print("3. Start chatting")
                try:
                    choice = int(input())
                except ValueError:
                    print("Input is wrong, Please input an integer")
                    continue
                if choice == 1:
                    await auth.change_password()
                elif choice == 2:
                    self.username = "guest"
                elif choice == 3:
                    await auth.chat()
                elif choice == 0:
                    break
                else :
                    print("Input correct option")        

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
print("Welcome to Messenger")
auth = Auth("127.0.0.1", 8888, loop)
asyncio.run(auth.run())
#run the programm to check implemented functions
#run()
#loop.run_forever()
loop.close()
