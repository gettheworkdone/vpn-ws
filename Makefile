VERSION=0.2

SHARED_OBJECTS=src/error.o src/tuntap.o src/memory.o src/bits.o src/base64.o src/exec.o src/websocket.o src/utils.o
OBJECTS=src/main.o $(SHARED_OBJECTS) src/socket.o src/event.o src/io.o src/uwsgi.o src/sha1.o src/macmap.o

SERVER_BIN=lollipop-server
CLIENT_BIN=lollipop-client
LEGACY_SERVER_BIN=vpn-ws
LEGACY_CLIENT_BIN=vpn-ws-client

ifeq ($(OS), Windows_NT)
	LIBS+=-lws2_32 -lsecur32
	SERVER_LIBS = -lws2_32
else
	OS=$(shell uname)
	ifeq ($(OS), Darwin)
		LIBS+=-framework Security -framework CoreFoundation
		CFLAGS+=-arch i386 -arch x86_64
	else
		LIBS+=-lcrypto -lssl
	endif
endif

all: $(SERVER_BIN) $(CLIENT_BIN) compat-bins

src/%.o: src/%.c src/vpn-ws.h
	$(CC) $(CFLAGS) -Wall -Werror -g -c -o $@ $<

$(SERVER_BIN): $(OBJECTS)
	$(CC) $(CFLAGS) $(LDFLAGS) -Wall -Werror -g -o $(SERVER_BIN) $(OBJECTS) $(SERVER_LIBS)

$(SERVER_BIN)-static: $(OBJECTS)
	$(CC) -static $(CFLAGS) $(LDFLAGS) -Wall -Werror -g -o $(SERVER_BIN) $(OBJECTS) $(SERVER_LIBS)

$(CLIENT_BIN): src/client.o src/ssl.o $(SHARED_OBJECTS)
	$(CC) $(CFLAGS) $(LDFLAGS) -Wall -Werror -g -o $(CLIENT_BIN) src/client.o src/ssl.o $(SHARED_OBJECTS) $(LIBS)

compat-bins: $(SERVER_BIN) $(CLIENT_BIN)
	cp $(SERVER_BIN) $(LEGACY_SERVER_BIN)
	cp $(CLIENT_BIN) $(LEGACY_CLIENT_BIN)

linux-tarball: $(SERVER_BIN)-static
	tar zcvf vpn-ws-$(VERSION)-linux-$(shell uname -m).tar.gz $(SERVER_BIN)

osxpkg: $(SERVER_BIN) $(CLIENT_BIN)
	mkdir -p dist/usr/bin
	cp $(SERVER_BIN) $(CLIENT_BIN) dist/usr/bin
	pkgbuild --root dist --identifier it.unbit.vpn-ws vpn-ws-$(VERSION)-osx.pkg

clean:
	rm -rf src/*.o $(SERVER_BIN) $(CLIENT_BIN) $(LEGACY_SERVER_BIN) $(LEGACY_CLIENT_BIN)
