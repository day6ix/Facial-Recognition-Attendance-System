const startMarkBtn = document.getElementById("startMarkBtn");
const stopMarkBtn = document.getElementById("stopMarkBtn");
const markVideo = document.getElementById("markVideo");
const markStatus = document.getElementById("markStatus");
const recognizedList = document.getElementById("recognizedList");
const statusText = document.getElementById("status");
const progressBar = document.getElementById("progressBar");

let markStream = null;
let markInterval = null;
let recognizedIds = new Set();
let livenessStep = "BLINK"; // BLINK → TURN → DONE

if (!markVideo || !statusText || !progressBar) {
  console.error("Missing required UI elements");
  throw new Error("UI init failed");
}

/* ---------- START ---------- */
startMarkBtn.addEventListener("click", async () => {
  livenessStep = "BLINK";
  recognizedIds.clear();

  startMarkBtn.disabled = true;
  stopMarkBtn.disabled = false;

  statusText.innerText = "Blink your eyes 👀";
  progressBar.style.width = "20%";

  try {
    markStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 }
    });

    markVideo.srcObject = markStream;
    await markVideo.play();

    markStatus.innerText = "Scanning...";
    markInterval = setInterval(captureAndRecognize, 1200);

  } catch (err) {
    alert("Camera error: " + err.message);
    startMarkBtn.disabled = false;
    stopMarkBtn.disabled = true;
  }
});

/* ---------- STOP ---------- */
stopMarkBtn.addEventListener("click", () => {
  if (markInterval) clearInterval(markInterval);
  if (markStream) markStream.getTracks().forEach(t => t.stop());

  startMarkBtn.disabled = false;
  stopMarkBtn.disabled = true;

  statusText.innerText = "Stopped";
  progressBar.style.width = "0%";
  markStatus.innerText = "Stopped";
});

/* ---------- MAIN LOOP ---------- */
async function captureAndRecognize() {
  const canvas = document.createElement("canvas");
  canvas.width = markVideo.videoWidth || 640;
  canvas.height = markVideo.videoHeight || 480;
  canvas.getContext("2d").drawImage(markVideo, 0, 0);

  const blob = await new Promise(r => canvas.toBlob(r, "image/jpeg", 0.85));
  const fd = new FormData();
  fd.append("image", blob, "frame.jpg");

  try {
    const res = await fetch("/recognize_face", {
      method: "POST",
      body: fd
    });

    const j = await res.json();

    /* ---------- LIVENESS ---------- */
    if (livenessStep === "BLINK") {
      statusText.innerText = "Blink your eyes 👀";
      progressBar.style.width = "30%";
      if (j.blink === true) livenessStep = "TURN";
      return;
    }

    if (livenessStep === "TURN") {
      statusText.innerText = "Turn your head 👈 👉";
      progressBar.style.width = "60%";
      if (Math.abs(j.yaw) > 15) livenessStep = "DONE";
      return;
    }

    /* ---------- RECOGNITION ---------- */
    if (livenessStep === "DONE" && j.recognized) {
      statusText.innerText = "Verified ✅";
      progressBar.style.width = "100%";

      markStatus.innerText =
        `Recognized: ${j.name} (${Math.round(j.confidence * 100)}%)`;

      if (!recognizedIds.has(j.student_id)) {
        recognizedIds.add(j.student_id);
        const li = document.createElement("li");
        li.className = "list-group-item";
        li.innerText = `${j.name} — ${new Date().toLocaleTimeString()}`;
        recognizedList.prepend(li);
      }

      clearInterval(markInterval);
    }

  } catch (err) {
    console.error("Recognition error", err);
  }
}
