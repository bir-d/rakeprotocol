import sys
import server_library

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("[r.s]\tArgument error; usage <host> <port>")
        sys.exit(1)

    # Uses Parser object to populate client data.
    print("\n[r.s]\tServer initiated; executing core functionality.")
    server   = server_library.Server(sys.argv[1], sys.argv[2])
    server.s_initiate_connection()
    # server.open_socket()

  


