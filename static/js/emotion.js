/* ==========================================================================
   NeuroSense AI — Emotion Detection & Visualization
   ========================================================================== */

let emotionChart = null;
let emotionStream = null;
let emotionInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  initEmotionCamera();
  initEmotionControls();
  initEmotionChart();
  loadEmotionHistory();
});

/* ==========================================================================
   CAMERA
   ========================================================================== */

async function initEmotionCamera(){
  const video = document.getElementById("emotionVideo");

  if(!video) return;

  try{
    emotionStream = await navigator.mediaDevices.getUserMedia({
      video:true,
      audio:false
    });

    video.srcObject = emotionStream;
    await video.play();

    startEmotionLoop();

  }catch(err){
    console.error(err);
    toast("Camera access denied");
  }
}

/* ==========================================================================
   CONTROLS
   ========================================================================== */

function initEmotionControls(){
  const stopBtn = document.getElementById("stopEmotionBtn");
  const startBtn = document.getElementById("startEmotionBtn");

  if(stopBtn){
    stopBtn.addEventListener("click", stopEmotionDetection);
  }

  if(startBtn){
    startBtn.addEventListener("click", startEmotionLoop);
  }
}

/* ==========================================================================
   DETECTION LOOP
   ========================================================================== */

function startEmotionLoop(){
  if(emotionInterval) return;

  emotionInterval = setInterval(async () => {
    await detectEmotion();
  }, 2500);

  setEmotionStatus("Emotion tracking active");
}

function stopEmotionDetection(){
  if(emotionInterval){
    clearInterval(emotionInterval);
    emotionInterval = null;
  }

  if(emotionStream){
    emotionStream.getTracks().forEach(track => track.stop());
  }

  setEmotionStatus("Emotion tracking stopped");
}

/* ==========================================================================
   DETECT EMOTION
   ========================================================================== */

async function detectEmotion(){
  const video = document.getElementById("emotionVideo");
  const canvas = document.getElementById("emotionCanvas");

  if(!video || !canvas) return;

  const ctx = canvas.getContext("2d");

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;

  ctx.drawImage(video,0,0,canvas.width,canvas.height);

  const image =
    canvas.toDataURL("image/jpeg",0.7);

  try{
    const res = await fetch("/api/detect_emotion", {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body:JSON.stringify({ image })
    });

    const data = await res.json();

    if(data.error){
      throw new Error(data.error);
    }

    updateEmotionUI(data);
    addEmotionToHistory(data);

  }catch(err){
    console.error(err);
    setEmotionStatus("Detection failed");
  }
}

/* ==========================================================================
   UPDATE UI
   ========================================================================== */

function updateEmotionUI(data){
  const emotion =
    data.emotion || "neutral";

  const confidence =
    parseFloat(data.confidence || 0);

  setText("currentEmotion", emotion);
  setText(
    "emotionConfidence",
    confidence.toFixed(1) + "%"
  );

  setEmotionStatus(
    `Detected ${emotion}`
  );

  animateConfidence(confidence);

  updateEmotionChart(data.scores || {});
}

/* ==========================================================================
   CONFIDENCE BAR
   ========================================================================== */

function animateConfidence(value){
  const bar =
    document.getElementById(
      "emotionConfidenceBar"
    );

  if(!bar) return;

  bar.style.width =
    `${Math.min(value,100)}%`;

  if(value > 75){

    bar.style.background =
      "linear-gradient(90deg,#00e5aa,#4fd1ff)";

  }else if(value > 45){

    bar.style.background =
      "linear-gradient(90deg,#ffc857,#ff9f43)";

  }else{

    bar.style.background =
      "linear-gradient(90deg,#ff5d7a,#ff8fab)";
  }
}

/* ==========================================================================
   CHART
   ========================================================================== */

function initEmotionChart(){
  const ctx =
    document.getElementById("emotionChart");

  if(!ctx) return;

  emotionChart = new Chart(ctx, {

    type:"radar",

    data:{
      labels:[
        "Happy",
        "Sad",
        "Neutral",
        "Stress",
        "Calm",
        "Angry"
      ],

      datasets:[{
        label:"Emotion Intensity",

        data:[50,20,60,15,70,10],

        borderColor:"#7c6fff",

        backgroundColor:
          "rgba(124,111,255,.18)",

        pointBackgroundColor:"#fff",

        borderWidth:2
      }]
    },

    options:{
      responsive:true,

      scales:{
        r:{
          angleLines:{
            color:"rgba(255,255,255,.08)"
          },

          grid:{
            color:"rgba(255,255,255,.08)"
          },

          pointLabels:{
            color:"#fff"
          },

          ticks:{
            display:false
          }
        }
      },

      plugins:{
        legend:{
          labels:{
            color:"#fff"
          }
        }
      }
    }

  });
}

function updateEmotionChart(scores){

  if(!emotionChart) return;

  emotionChart.data.datasets[0].data = [
    scores.happy || 0,
    scores.sad || 0,
    scores.neutral || 0,
    scores.stress || 0,
    scores.calm || 0,
    scores.angry || 0
  ];

  emotionChart.update();
}

/* ==========================================================================
   HISTORY
   ========================================================================== */

let emotionHistory = [];

function addEmotionToHistory(data){

  emotionHistory.unshift({
    emotion:data.emotion,
    confidence:data.confidence,
    time:new Date().toLocaleTimeString()
  });

  if(emotionHistory.length > 10){
    emotionHistory.pop();
  }

  renderEmotionHistory();
}

function renderEmotionHistory(){
  const list =
    document.getElementById(
      "emotionHistory"
    );

  if(!list) return;

  list.innerHTML =
    emotionHistory.map((item)=>{

      return `
        <div class="emotion-history-item">
          <div class="emotion-history-left">
            <div class="emotion-badge">
              ${escapeHtml(item.emotion)}
            </div>
          </div>

          <div class="emotion-history-right">
            <div>
              ${escapeHtml(item.confidence.toFixed(1))}%
            </div>

            <small>
              ${escapeHtml(item.time)}
            </small>
          </div>
        </div>
      `;

    }).join("");
}

async function loadEmotionHistory(){

  try{
    const res =
      await fetch("/api/emotion_history");

    const data =
      await res.json();

    if(Array.isArray(data.history)){

      emotionHistory = data.history;

      renderEmotionHistory();
    }

  }catch(err){
    console.error(err);
  }
}

/* ==========================================================================
   STATUS
   ========================================================================== */

function setEmotionStatus(text){
  setText("emotionStatus", text);
}

/* ==========================================================================
   HELPERS
   ========================================================================== */

function setText(id,value){
  const el =
    document.getElementById(id);

  if(el){
    el.textContent = value;
  }
}

function escapeHtml(text){
  return String(text)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;");
}

/* ==========================================================================
   TOAST
   ========================================================================== */

function toast(message){

  const t =
    document.createElement("div");

  t.className = "toast";

  t.textContent = message;

  document.body.appendChild(t);

  setTimeout(()=>{

    t.style.opacity = "0";

    t.style.transform =
      "translateY(12px)";

    t.style.transition = ".25s";

    setTimeout(()=>{
      t.remove();
    },300);

  },3000);
}

/* ==========================================================================
   CLEANUP
   ========================================================================== */

window.addEventListener("beforeunload", () => {

  if(emotionInterval){
    clearInterval(emotionInterval);
  }

  if(emotionStream){
    emotionStream.getTracks().forEach(track => track.stop());
  }

});