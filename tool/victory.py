from wave import open


def victory(file):
    print("*" * 40)
    print("\    / | ----- ----- ----- |--\ / |")
    print(" \  /  | |     |  |  ||__/ | |")
    print("  \/   | _____  |   ____ | \ | .")
    print("*" * 40)
    try:
        from pyaudio import PyAudio
    except Exception as e:
        print(e)
        return 0
    chunk = 1024
    f = open(file, "r")

    p = PyAudio()

    stream = p.open(format=p.get_format_from_width(f.getsampwidth()), channels=f.getnchannels(),
                    rate=f.getframerate(), output=True)
    data = f.readframes(chunk)

    while len(data) > 0:
        stream.write(data)
        data = f.readframes(chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()
