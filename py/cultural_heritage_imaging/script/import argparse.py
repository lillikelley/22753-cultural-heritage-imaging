import argparse

def main():
    parser = argparse.ArgumentParser(description="Example CLI Tool")
    parser.add_argument('action', choices=['start', 'stop'], help="Action to perform")
    parser.add_argument('--port', type=str, default='COM3', help="Serial port for the device")
    
    args = parser.parse_args()
    
    if args.action == "start":
        print(f"Starting the device on port {args.port}")
    elif args.action == "stop":
        print("Stopping the device")

if __name__ == "__main__":
    main()
