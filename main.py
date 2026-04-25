import os, requests, subprocess, time, base64
from flask import Flask, request, send_file

app = Flask(__name__)

def download_file(url, path):
      try:
                r = requests.get(url, stream=True, timeout=30)
                with open(path, "wb") as f:
                              for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                                    except: pass

  @app.route("/", methods=["POST"])
def render():
      data = request.json
    scenes = data.get("scenes", [])
    fps = data.get("fps", 30)
    tmp = f"render_{int(time.time())}"
    os.makedirs(tmp, exist_ok=True)

    video_parts = []
    for i, s in enumerate(scenes):
              img = os.path.join(tmp, f"i_{i}.jpg")
        aud = os.path.join(tmp, f"a_{i}.mp3")
        out = os.path.join(tmp, f"v_{i}.mp4")

        download_file(s["imageUrl"], img)
        if s.get("audioBase64"):
                      with open(aud, "wb") as f: f.write(base64.b64decode(s["audioBase64"]))
        else:
            subprocess.run(f"ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 5 -q:a 9 {aud} -y", shell=True)

        kb = "scale=3840:-2,zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1920x1080"
        cmd = f"ffmpeg -loop 1 -i {img} -i {aud} -vf \"{kb},format=yuv420p\" -t 5 -c:v libx264 -preset fast -crf 23 -c:a aac -shortest {out} -y"
        subprocess.run(cmd, shell=True)
        video_parts.append(out)

    list_p = os.path.join(tmp, "list.txt")
    with open(list_p, "w") as f:
              for v in video_parts: f.write(f"file '{os.path.basename(v)}'\n")

    final = os.path.join(tmp, "final.mp4")
    subprocess.run(f"ffmpeg -f concat -safe 0 -i {list_p} -c copy {final} -y", shell=True)
    return send_file(final, mimetype="video/mp4")

if __name__ == "__main__":
      app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
