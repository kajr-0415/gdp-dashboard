import streamlit as st
import numpy as np
from PIL import Image
import base64, sys, io, math
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="PAN-MED | Skin Cancer Detection",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

def img_b64(name):
    p = APP_DIR / name
    if p.exists():
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def data_uri(name):
    b = img_b64(name)
    return f"data:image/png;base64,{b}" if b else ""

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800;900&display=swap');
*{font-family:'Poppins',sans-serif;box-sizing:border-box;margin:0;padding:0;}
html,body,.stApp{background:#1a0a2e;color:#fff;overflow-x:hidden;}
#MainMenu,footer,header,[data-testid="stToolbar"]{visibility:hidden;height:0;}
.block-container{padding:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none;}

/* NAV BUTTONS — override Streamlit default inside nav columns */
div[data-testid="stHorizontalBlock"]:first-of-type .stButton>button {
  background:none!important;
  border:none!important;
  color:rgba(200,160,255,0.75)!important;
  font-size:13.5px!important;
  font-weight:600!important;
  padding:8px 18px!important;
  border-radius:20px!important;
  box-shadow:none!important;
  width:auto!important;
  margin-top:6px;
}
div[data-testid="stHorizontalBlock"]:first-of-type .stButton>button:hover {
  background:rgba(150,50,255,0.22)!important;
  color:#fff!important;
}
div[data-testid="stHorizontalBlock"]:first-of-type {
  background:rgba(12,3,28,0.97);
  border-bottom:1px solid rgba(160,80,255,0.22);
  position:sticky;top:0;z-index:999;
  backdrop-filter:blur(16px);
  padding:4px 12px;
}

/* NAV (old html version - hidden) */
.nav{display:none;}
.nav{
  position:sticky;top:0;z-index:999;
  background:rgba(12,3,28,0.97);
  backdrop-filter:blur(16px);
  border-bottom:1px solid rgba(160,80,255,0.22);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 40px;height:62px;
}
.nav-logo{color:#fff;font-size:17px;font-weight:800;letter-spacing:1px;display:flex;align-items:center;gap:8px;}
.nav-logo em{color:#cc44ff;font-style:normal;}
.nav-links{display:flex;gap:4px;}
.nav-btn{
  background:none;border:none;cursor:pointer;
  color:rgba(200,160,255,0.7);font-size:13.5px;font-weight:600;
  padding:8px 22px;border-radius:20px;transition:all .2s;
}
.nav-btn:hover{color:#fff;background:rgba(150,50,255,0.18);}
.nav-btn.active{
  background:linear-gradient(135deg,#5500cc,#9900ff);
  color:#fff;box-shadow:0 4px 16px rgba(150,0,255,0.35);
}

/* FULL-WIDTH IMAGE SECTIONS */
.canva-sec{width:100%;display:block;line-height:0;}
.canva-sec img{width:100%;height:auto;display:block;}

/* SCAN SECTION */
.scan-wrap{
  background:linear-gradient(150deg,#3a0a8f 0%,#7c1fc4 32%,#b026d6 58%,#7c1fc4 82%,#4a0aa8 100%);
  padding:64px 5vw 72px;
  position:relative;overflow:hidden;
}
.scan-wrap::before{
  content:'';position:absolute;inset:0;
  background:
    radial-gradient(ellipse at 15% 20%,rgba(255,255,255,0.16) 0%,transparent 45%),
    radial-gradient(ellipse at 85% 15%,rgba(255,120,220,0.28) 0%,transparent 55%),
    radial-gradient(ellipse at 30% 90%,rgba(160,0,255,0.30) 0%,transparent 60%);
  pointer-events:none;
}
.scan-inner{max-width:820px;margin:0 auto;position:relative;z-index:1;}
.scan-head{text-align:center;margin-bottom:36px;}
.scan-head h2{font-size:clamp(22px,3.5vw,34px);font-weight:800;margin-bottom:6px;}
.scan-head h2 em{color:#ffd6fb;font-style:normal;}
.scan-head p{color:rgba(255,235,255,0.75);font-size:13.5px;}
.cam-orb{
  display:flex;flex-direction:column;align-items:center;margin-bottom:32px;
}
.cam-orb-icon{
  display:inline-flex;align-items:center;justify-content:center;
  width:110px;height:110px;
  background:linear-gradient(135deg,#7c1fe0,#e83fd6);
  border-radius:28px;font-size:50px;
  box-shadow:0 14px 44px rgba(210,0,255,0.55),inset 0 2px 8px rgba(255,255,255,0.35);
  margin-bottom:16px;position:relative;overflow:hidden;
}
.cam-orb-icon::after{
  content:'';position:absolute;top:-30%;left:-20%;width:140%;height:70%;
  background:linear-gradient(160deg,rgba(255,255,255,0.35),transparent 60%);
  transform:rotate(-8deg);pointer-events:none;
}
.cam-orb span{color:#fff;font-size:24px;font-weight:800;text-shadow:0 0 22px rgba(255,140,255,0.55);}
.cam-orb small{color:rgba(255,235,255,0.85);font-size:12.5px;margin-top:6px;max-width:360px;text-align:center;line-height:1.5;}

/* TABS */
.stTabs [data-baseweb="tab-list"]{
  background:rgba(255,255,255,0.10);border-radius:16px;
  gap:4px;padding:5px;border:1px solid rgba(255,255,255,0.22);
  max-width:460px;margin:0 auto 24px;
}
.stTabs [data-baseweb="tab"]{
  color:rgba(255,255,255,0.8)!important;
  font-weight:700;font-size:14px;border-radius:12px;padding:11px 30px;
}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,#7c1fe0,#e83fd6)!important;
  color:#fff!important;box-shadow:0 6px 18px rgba(210,0,255,0.45);
}
[data-testid="stFileUploader"]{
  background:rgba(255,255,255,0.08);
  border:2px dashed rgba(255,255,255,0.35);border-radius:18px;
}
[data-testid="stFileUploader"] label{color:rgba(255,240,255,0.9)!important;}
[data-testid="stFileUploader"] section{background:rgba(15,0,35,0.35)!important;border-radius:14px!important;}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small{color:rgba(255,240,255,0.75)!important;}
[data-testid="stBaseButton-secondary"]{
  background:#fff!important;color:#1a0a2e!important;border-radius:10px!important;font-weight:700!important;
}

/* BUTTON */
.stButton>button{
  background:linear-gradient(135deg,#4400bb,#9900ff)!important;
  color:#fff!important;border:none!important;
  border-radius:14px!important;font-weight:700!important;
  font-size:15px!important;padding:14px 36px!important;
  box-shadow:0 8px 28px rgba(140,0,255,0.4)!important;width:100%;
}
.stButton>button:hover{box-shadow:0 10px 36px rgba(140,0,255,0.6)!important;}

/* RESULT CARDS */
.rc{
  background:linear-gradient(140deg,rgba(18,0,50,0.95),rgba(35,0,80,0.9));
  border:1px solid rgba(140,70,255,0.3);border-radius:20px;
  padding:22px;margin-bottom:16px;
}
.rc-title{color:#fff;font-size:15px;font-weight:700;margin-bottom:12px;}
.rc-sub{color:rgba(190,140,255,0.6);font-size:10px;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;}
.diag-name{color:#fff;font-size:19px;font-weight:800;line-height:1.2;margin-bottom:3px;}
.diag-code{color:rgba(190,140,255,0.6);font-size:11px;font-family:monospace;}
.rbadge{padding:5px 14px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;}
.b-red{background:rgba(255,70,70,.18);color:#ff7070;border:1px solid rgba(255,70,70,.4);}
.b-orange{background:rgba(255,155,0,.18);color:#ffb347;border:1px solid rgba(255,155,0,.4);}
.b-yellow{background:rgba(255,220,0,.15);color:#ffd166;border:1px solid rgba(255,210,0,.4);}
.b-green{background:rgba(0,220,140,.15);color:#06d6a0;border:1px solid rgba(0,220,140,.35);}
.conf-row{display:flex;justify-content:space-between;color:rgba(195,150,255,.8);font-size:12px;margin-bottom:6px;}
.conf-row strong{color:#fff;}
.conf-bg{background:rgba(70,0,160,.35);border-radius:10px;height:11px;overflow:hidden;}
.conf-fill{height:100%;border-radius:10px;background:linear-gradient(90deg,#4400bb,#cc00ff);}
.pred-row{display:flex;align-items:center;gap:10px;margin-bottom:9px;}
.pred-name{color:rgba(195,150,255,.85);font-size:10.5px;flex:0 0 210px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.pred-bar-bg{flex:1;background:rgba(70,0,160,.28);border-radius:6px;height:7px;overflow:hidden;}
.pred-bar{height:100%;border-radius:6px;background:linear-gradient(90deg,#4400bb,#cc00ff);}
.pred-pct{color:rgba(195,150,255,.7);font-size:11px;flex:0 0 38px;text-align:right;}
.impl-box{
  background:rgba(70,0,160,.14);
  border:1px solid rgba(140,70,255,.25);border-left:3px solid #9900ff;
  border-radius:14px;padding:16px;
}
.impl-cat{color:#c77dff;font-size:11.5px;font-weight:700;margin-bottom:8px;}
.impl-text{color:rgba(215,185,255,.85);font-size:11.5px;line-height:1.72;margin-bottom:10px;}
.chip{
  display:inline-block;background:rgba(110,0,230,.22);color:#c77dff;
  border:1px solid rgba(150,70,255,.32);border-radius:20px;
  padding:3px 11px;font-size:10px;margin:3px 3px 0 0;
}
.disc{
  background:rgba(255,160,0,.07);border:1px solid rgba(255,160,0,.22);
  border-radius:11px;padding:11px 14px;margin-top:14px;
  color:rgba(255,210,120,.8);font-size:10.5px;line-height:1.65;
}
.gcam-label{color:rgba(195,150,255,.7);font-size:10.5px;text-align:center;margin-top:4px;}

/* REPORT LETTERHEAD */
.report-shell{
  background:linear-gradient(160deg,rgba(15,0,40,0.55),rgba(25,0,60,0.35));
  border:1px solid rgba(140,70,255,0.22);border-radius:24px;
  padding:22px 22px 4px;margin-bottom:16px;
}
.report-head{
  display:flex;align-items:flex-start;justify-content:space-between;
  border-bottom:1px solid rgba(150,70,255,0.25);
  padding-bottom:16px;margin-bottom:18px;flex-wrap:wrap;gap:10px;
}
.report-brand{display:flex;flex-direction:column;gap:3px;}
.report-brand .brand-line{color:#fff;font-size:16px;font-weight:800;}
.report-brand .brand-line span{color:#cc44ff;}
.report-brand small{color:rgba(195,150,255,.55);font-size:10.5px;font-weight:500;letter-spacing:.3px;}
.report-meta{color:rgba(195,150,255,.6);font-size:11px;text-align:right;line-height:1.7;}
.report-meta b{color:#fff;font-family:monospace;font-weight:600;}

/* HERO DIAGNOSIS CARD */
.hero-card{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;}
.hero-left{display:flex;flex-direction:column;gap:8px;}
.hero-ring{position:relative;width:104px;height:104px;flex:0 0 auto;}
.hero-ring svg{width:100%;height:100%;transform:rotate(-90deg);}
.ring-bg{fill:none;stroke:rgba(70,0,160,.35);stroke-width:10;}
.ring-fg{fill:none;stroke:#b347ff;stroke-width:10;stroke-linecap:round;transition:stroke-dashoffset .6s ease;}
.ring-label{
  position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
}
.ring-label strong{color:#fff;font-size:20px;font-weight:800;line-height:1.1;}
.ring-label span{color:rgba(195,150,255,.6);font-size:8.5px;letter-spacing:.6px;text-transform:uppercase;margin-top:2px;}

/* CHIP GRID (recommended actions) */
.chip-grid{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;}

/* EMAIL/PDF ACTION BAR */
.action-row{display:flex;gap:12px;margin-top:8px;flex-wrap:wrap;}
.act-btn{
  flex:1;min-width:140px;
  background:linear-gradient(135deg,rgba(80,0,180,.5),rgba(130,0,255,.4));
  border:1px solid rgba(150,70,255,.4);border-radius:13px;
  padding:13px 16px;color:#fff;font-size:13px;font-weight:600;
  text-align:center;cursor:pointer;display:block;text-decoration:none;
  transition:all .2s;
}
.act-btn:hover{background:linear-gradient(135deg,#4400bb,#9900ff);box-shadow:0 6px 20px rgba(140,0,255,.4);color:#fff;}

/* ABOUT PAGE */
.about-wrap{width:100%;line-height:0;}
.about-wrap img{width:100%;height:auto;display:block;}

/* CONTACT PAGE */
.contact-outer{
  display:flex;min-height:100vh;
}
.contact-left{
  flex:0 0 40%;
  background:linear-gradient(160deg,#281549 0%,#1a0040 100%);
  display:flex;align-items:center;justify-content:center;padding:60px 40px;
}
.contact-left h1{font-size:clamp(32px,4vw,58px);font-weight:900;color:#fff;line-height:1.1;}
.contact-right{flex:1;background:#f0f0f0;}
.contact-right iframe{width:100%;height:100vh;border:none;display:block;}

.stSpinner>div{border-top-color:#9900ff!important;}
.demo-notice{
  background:rgba(0,180,255,.08);border:1px solid rgba(0,180,255,.25);
  border-radius:11px;padding:10px 14px;margin-bottom:20px;
  color:rgba(140,210,255,.85);font-size:10.5px;line-height:1.6;
}
</style>
""", unsafe_allow_html=True)

# ── Load model + modules ──────────────────────────────────────────────────────
from model_utils import load_model, predict
from implications import IMPLICATIONS, CLASS_NAMES, CLASS_CODES, RISK_TIER
import cv2 as _cv2, tensorflow as _tf
from PIL import Image as _PIL

@st.cache_resource(show_spinner=False)
def get_model():
    return load_model()

with st.spinner("🔬 Loading PAN-MED model…"):
    model = get_model()

is_demo = not (APP_DIR/"model.keras").exists() and not (APP_DIR/"model.h5").exists()

# ── Session state ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

# ── NAV — real Streamlit buttons ──────────────────────────────────────────────
_nav_c1, _nav_c2, _nav_c3, _nav_c4, _nav_c5 = st.columns([3, 1, 1, 1, 4])
with _nav_c1:
    st.markdown('<div style="color:#fff;font-size:17px;font-weight:800;padding:14px 0 0 8px;">✕ PAN<span style=\"color:#cc44ff\">MED</span></div>', unsafe_allow_html=True)
with _nav_c2:
    if st.button("Home", key="nb_home"):
        st.session_state.page = "home"; st.rerun()
with _nav_c3:
    if st.button("About", key="nb_about"):
        st.session_state.page = "about"; st.rerun()
with _nav_c4:
    if st.button("Contact", key="nb_contact"):
        st.session_state.page = "contact"; st.rerun()

page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
if page == "home":

    # P1S1 — Hero
    st.markdown(f'<div class="canva-sec"><img src="{data_uri("P1S1.png")}" /></div>', unsafe_allow_html=True)

    # P1S2 — Brief Description
    st.markdown(f'<div class="canva-sec"><img src="{data_uri("P1S2.png")}" /></div>', unsafe_allow_html=True)

    # Features
    st.markdown(f'<div class="canva-sec"><img src="{data_uri("Features.png")}" /></div>', unsafe_allow_html=True)

    # ── SCAN SECTION ──────────────────────────────────────────────────────────
    st.markdown('<div class="scan-wrap"><div class="scan-inner">', unsafe_allow_html=True)

    st.markdown("""
    <div class="scan-head">
      <div class="cam-orb">
        <div class="cam-orb-icon">📷</div>
        <span>Camera Button</span>
        <small>Capture or upload a dermatoscopic image to begin skin cancer detection</small>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if is_demo:
        st.markdown('<div class="demo-notice"><strong>Demo Mode:</strong> No model.keras found — running with a demo model. Drop your trained model.keras into the project folder for real predictions.</div>', unsafe_allow_html=True)

    tab_cam, tab_up = st.tabs(["📷  Camera Capture", "📁  Upload Image"])
    image_input = None

    with tab_cam:
        cam_img = st.camera_input("Point camera at the skin lesion")
        if cam_img:
            image_input = Image.open(cam_img).convert("RGB")

    with tab_up:
        up_file = st.file_uploader("Upload a dermatoscopic image", type=["jpg","jpeg","png","bmp","webp"])
        if up_file:
            image_input = Image.open(up_file).convert("RGB")

    if image_input:
        st.markdown('<p style="text-align:center;color:rgba(195,150,255,.65);font-size:12px;margin:8px 0 14px;">Image loaded — press Scan to analyze</p>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            scan = st.button("Scan for Results")

        if scan:
            with st.spinner("Analyzing with PAN-MED CNN + GradCAM…"):
                idx, confidence, all_probs = predict(model, image_input)

            name  = CLASS_NAMES[idx]
            code  = CLASS_CODES[idx]
            conf  = confidence * 100
            tier  = RISK_TIER.get(code, "yellow")
            impl  = IMPLICATIONS.get(code, IMPLICATIONS["DEFAULT"])

            bmap  = {"red":("b-red","HIGH RISK"),"orange":("b-orange","PRE-MALIGNANT"),
                     "yellow":("b-yellow","MONITOR"),"green":("b-green","BENIGN")}
            bcls, btxt = bmap[tier]

            # ── GradCAM (computed once, cached in session_state) ────────────────
            _sz   = (224,224)
            _imgr = image_input.resize(_sz)
            _orig = np.array(_imgr)
            _arr  = _orig.astype(np.float32)/255.0

            _conv_name  = None
            _conv_model = model
            for _l in reversed(model.layers):
                if isinstance(_l, _tf.keras.layers.Conv2D):
                    _conv_name = _l.name; break
            if not _conv_name:
                for _l in reversed(model.layers):
                    if isinstance(_l, _tf.keras.Model):
                        for _sl in reversed(_l.layers):
                            if isinstance(_sl, _tf.keras.layers.Conv2D):
                                _conv_name  = _sl.name
                                _conv_model = _l; break
                    if _conv_name: break

            gradcam_imgs, gradcam_error = None, None
            try:
                _gm = _tf.keras.models.Model(
                    inputs=_conv_model.inputs,
                    outputs=[_conv_model.get_layer(_conv_name).output, _conv_model.output]
                )
                with _tf.GradientTape() as _tape:
                    _out = _gm(np.expand_dims(_arr,0))
                    _co  = _out[0]; _pr = _out[1]
                    if isinstance(_pr, list): _pr = _pr[-1]
                    _tape.watch(_co)
                    _pi  = int(_tf.argmax(_pr[0]).numpy())
                    _cc  = _pr[:, _pi]
                _gr  = _tape.gradient(_cc, _co)
                _pg  = _tf.reduce_mean(_gr, axis=(0,1,2))
                _co  = _co[0]
                _hm  = _tf.squeeze(_co @ _pg[...,_tf.newaxis])
                _hm  = (_tf.maximum(_hm,0)/(_tf.math.reduce_max(_hm)+1e-8)).numpy()
                _hmr = _cv2.resize(_hm, _sz)
                _hmu = np.uint8(255*_hmr)
                _hmc = _cv2.cvtColor(_cv2.applyColorMap(_hmu,_cv2.COLORMAP_JET),_cv2.COLOR_BGR2RGB)
                _ov  = _cv2.addWeighted(_orig,0.6,_hmc,0.4,0)
                gradcam_imgs = (_imgr, _PIL.fromarray(_hmc), _PIL.fromarray(_ov))
            except Exception as _e:
                gradcam_error = str(_e)

            top5_idx = np.argsort(all_probs)[::-1][:5]
            top5 = [(CLASS_NAMES[i], float(all_probs[i]*100)) for i in top5_idx]

            # Persist everything needed to render + export, so the report
            # survives later reruns (e.g. clicking Download PDF or Send Email).
            st.session_state.result = dict(
                name=name, code=code, conf=conf, tier=tier, impl=impl,
                bcls=bcls, btxt=btxt, gradcam_imgs=gradcam_imgs,
                gradcam_error=gradcam_error, top5=top5,
                report_id="PM-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                generated_at=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
            )

    # ── Persistent report render (survives PDF/email button reruns) ────────────
    result = st.session_state.get("result")
    if result:
        name          = result["name"]
        code          = result["code"]
        conf          = result["conf"]
        tier          = result["tier"]
        impl          = result["impl"]
        bcls          = result["bcls"]
        btxt          = result["btxt"]
        top5          = result["top5"]
        report_id     = result["report_id"]
        generated_at  = result["generated_at"]
        gradcam_imgs  = result["gradcam_imgs"]

        circumference = 2 * math.pi * 52
        ring_offset   = circumference * (1 - min(conf, 100) / 100)

        # ── Report letterhead ────────────────────────────────────────────
        st.markdown(f"""
        <div class="report-shell">
          <div class="report-head">
            <div class="report-brand"><div class="brand-line">✕ PAN<span>MED</span></div><small>AI-Assisted Dermatological Screening Report</small></div>
            <div class="report-meta"><div>Report ID&nbsp;<b>{report_id}</b></div><div>{generated_at}</div></div>
          </div>
        """, unsafe_allow_html=True)

        # ── Hero diagnosis card with confidence ring ─────────────────────
        st.markdown(f"""
        <div class="rc hero-card">
          <div class="hero-left">
            <div class="rc-sub">PRIMARY FINDING</div>
            <div class="diag-name">{name}</div>
            <div class="diag-code">Code: {code.upper()}</div>
            <span class="rbadge {bcls}">{btxt}</span>
          </div>
          <div class="hero-ring">
            <svg viewBox="0 0 120 120">
              <circle class="ring-bg" cx="60" cy="60" r="52"></circle>
              <circle class="ring-fg" cx="60" cy="60" r="52"
                style="stroke-dasharray:{circumference:.1f};stroke-dashoffset:{ring_offset:.1f}"></circle>
            </svg>
            <div class="ring-label"><strong>{conf:.0f}%</strong><span>Confidence</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── GradCAM ───────────────────────────────────────────────────────
        st.markdown('<div class="rc"><div class="rc-title">GradCAM Visualization</div>'
                     '<div class="rc-sub">Original · Heatmap · Overlay — regions driving the AI\'s decision</div>',
                     unsafe_allow_html=True)
        if gradcam_imgs:
            co, ch, cv_ = st.columns(3)
            for col, im, lab in zip((co, ch, cv_), gradcam_imgs,
                                     ("Original", "Grad-CAM Heatmap", "Overlay")):
                with col:
                    st.image(im, use_container_width=True)
                    st.markdown(f'<div class="gcam-label">{lab}</div>', unsafe_allow_html=True)
        else:
            st.info(f"GradCAM unavailable: {result.get('gradcam_error') or 'unknown error'}")
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Top 5 ─────────────────────────────────────────────────────────
        st.markdown('<div class="rc"><div class="rc-title">Top 5 Predictions</div>', unsafe_allow_html=True)
        for cname, pct in top5:
            st.markdown(f"""
            <div class="pred-row">
              <div class="pred-name">{cname}</div>
              <div class="pred-bar-bg"><div class="pred-bar" style="width:{min(pct,100):.1f}%"></div></div>
              <div class="pred-pct">{pct:.1f}%</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Clinical Implications ────────────────────────────────────────
        chips = "".join(f'<span class="chip">✓ {a}</span>' for a in impl["actions"])
        st.markdown(f"""
        <div class="rc">
          <div class="rc-title">Clinical Implications</div>
          <div class="impl-box">
            <div class="impl-cat">{impl['category']}</div>
            <div class="impl-text">{impl['description']}</div>
            <div class="chip-grid">{chips}</div>
          </div>
          <div class="disc"><strong>Medical Disclaimer:</strong> PAN-MED is an AI-assisted screening
          tool and does <strong>not</strong> replace professional medical diagnosis. Always consult a
          licensed dermatologist for accurate evaluation and treatment.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # close report-shell

        # ── Export: real PDF + real email ────────────────────────────────
        st.markdown('<div class="rc"><div class="rc-title">Share / Export Results</div>', unsafe_allow_html=True)

        pdf_bytes = None
        try:
            from report_generator import generate_pdf_report
            gcam_o, gcam_h, gcam_ov = gradcam_imgs if gradcam_imgs else (None, None, None)
            pdf_bytes = generate_pdf_report(
                diagnosis_name=name, diagnosis_code=code, confidence=conf,
                risk_label=btxt, risk_tier=tier, top5=top5, implication=impl,
                gradcam_original=gcam_o, gradcam_heatmap=gcam_h, gradcam_overlay=gcam_ov,
                report_id=report_id, generated_at=generated_at,
            )
        except Exception as _e:
            st.error(f"PDF generation error: {_e}")

        ea, eb = st.columns(2)
        with ea:
            if pdf_bytes:
                st.download_button(
                    label="📄  Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"PANMED_{code.upper()}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.info("PDF export is unavailable — see error above.")
        with eb:
            with st.popover("✉️  Email Report", use_container_width=True):
                to_email = st.text_input("Recipient email", key="email_to", placeholder="doctor@example.com")
                if st.button("Send Report", key="send_email_btn", use_container_width=True):
                    if not to_email or "@" not in to_email:
                        st.warning("Enter a valid email address.")
                    elif not pdf_bytes:
                        st.warning("PDF isn't ready yet — see the error above.")
                    else:
                        try:
                            from email_utils import send_report_email, EmailConfigError
                            with st.spinner("Sending…"):
                                send_report_email(
                                    to_email=to_email, diagnosis_name=name, diagnosis_code=code,
                                    confidence=conf, risk_label=btxt, risk_tier=tier,
                                    category=impl["category"], description=impl["description"],
                                    actions=impl["actions"], pdf_bytes=pdf_bytes,
                                    pdf_filename=f"PANMED_{code.upper()}_report.pdf",
                                )
                            st.success(f"Report sent to {to_email}.")
                        except EmailConfigError as e:
                            st.warning(str(e))
                        except Exception as e:
                            st.error(f"Couldn't send email: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)  # close scan-inner + scan-wrap

    st.markdown(f'<div class="canva-sec"><img src="{data_uri("P1S3.png")}" /></div>', unsafe_allow_html=True)

elif page == "about":
    st.markdown(f'<div class="about-wrap"><img src="{data_uri("P2S1.png")}" /></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="canva-sec"><img src="{data_uri("P2S2.png")}" /></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONTACT PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "contact":
    st.markdown("""
    <div class="contact-outer">
      <div class="contact-left">
        <h1>Contact Page</h1>
      </div>
      <div class="contact-right">
        <iframe src="https://form.jotform.com/260524715952055"
          allowfullscreen allow="geolocation; microphone; camera">
        </iframe>
      </div>
    </div>
    """, unsafe_allow_html=True)