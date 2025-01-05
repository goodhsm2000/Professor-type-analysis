from pydub import AudioSegment


for k in range(1,4):
    input_file = "raw/hw_{}.mp3".format(k)
    print(input_file)
    audio = AudioSegment.from_mp3(input_file)

    duration = len(audio)
    segment_duration = 10000

    for i in range(0, duration, segment_duration):
        segment = audio[i:i + segment_duration]
        segment.export(f"pre/hw_{k}/output_{i // segment_duration + 1}.mp3", format="mp3")
