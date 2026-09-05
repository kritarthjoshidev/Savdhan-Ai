# Use an Android phone as a live CCTV camera

Savdhan AI accepts camera streams over RTSP, HTTP, or HTTPS. The phone must run
an IP-camera application that exposes a stream; a browser camera tab alone does
not expose a stream that the backend can consume.

## Steps

1. Connect the laptop and phone to the same Wi-Fi network.
2. In a phone IP-camera app, start the camera server and copy its **video
   stream** URL (not the app's control-page URL).
3. Open the frontend's **Live Camera Command** page and paste the URL into
   **Add phone / CCTV camera**.
4. Click **Test connection**. It must report that one frame was read.
5. Click **Save camera**, select a **Protection profile**, then click
   **Protect**. Use **Border** for a virtual-fence intrusion, **Traffic** for
   an accident scene, or **Auto** only when the camera context is not known.
6. The live preview shows annotated frames. A border crossing creates one
   `BORDER_INTRUSION`; a confirmed crash scene creates one
   `TRAFFIC_ACCIDENT`. Open **Incidents → Review** to watch the detection
   image, nearby frames, and short context clip before Verify/Reject.

## URL examples

Different phone apps use different paths. The app itself displays the exact
URL to copy. Common examples are:

```text
http://192.168.1.23:8080/video
rtsp://192.168.1.23:8554/live
```

Use the phone's actual LAN IP address, for example `192.168.1.23`. Do **not**
use `localhost` or `127.0.0.1`; on the laptop those point back to the laptop,
not to the phone.

## If the test fails

- Confirm both devices are on the same Wi-Fi, not guest Wi-Fi or mobile data.
- Keep the phone camera application open and disable battery optimisation for it.
- Re-copy the *video stream* URL from the phone app.
- Allow the backend through Windows Firewall on the private network if the
  frontend can access the backend but the backend cannot access the phone.
- If the backend runs in Docker, use the phone's LAN IP as above; never use a
  Docker container hostname in the phone URL.

Saved camera URLs are stored only in `backend/data/cameras.json`, which is
ignored by Git. The frontend receives a masked URL and never receives embedded
camera credentials.
