import streamlit as st
import json
import os
import random
import uuid

# --- Filstier ---
DATA_FILE      = "tasks.json"
STATS_FILE     = "stats.json"
SETTINGS_FILE  = "settings.json"

# --- Sideoppsett ---
st.set_page_config(page_title="Mine oppgaver", layout="centered")

# --- Last inn tasks ---
if "tasks" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            st.session_state.tasks = json.load(f)
    else:
        st.session_state.tasks = []
    # Gi ID til gamle tasks
    updated = False
    for t in st.session_state.tasks:
        if "id" not in t:
            t["id"] = str(uuid.uuid4())
            updated = True
    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.tasks, f, ensure_ascii=False, indent=2)

# --- Last inn statistikk ---
if "completed_count" not in st.session_state:
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            st.session_state.completed_count = json.load(f).get("completed", 0)
    else:
        st.session_state.completed_count = 0

# --- Default innstillinger (inkl. marquee-emoji) ---
default_settings = {
    "mode":    "GIF",
    "gif":     "https://media1.giphy.com/media/26tPplGWjN0xLybiU/giphy.gif",
    "img":     "https://imgflip.com/i/9uj9l8",
    "banner":  "🕹 LEVEL UP! YOU DID IT! 🕹",
    "marquee": "🚀"
}
if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_settings, f, ensure_ascii=False, indent=2)

settings = json.load(open(SETTINGS_FILE, "r", encoding="utf-8"))
for k, v in settings.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Hjelpefunksjoner ---
def save_tasks():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.tasks, f, ensure_ascii=False, indent=2)

def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"completed": st.session_state.completed_count}, f, ensure_ascii=False, indent=2)

def save_settings():
    s = {
        "mode":    st.session_state.mode,
        "gif":     st.session_state.gif,
        "img":     st.session_state.img,
        "banner":  st.session_state.banner,
        "marquee": st.session_state.marquee
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

# --- Bygg SURPRISE_HTML ut fra valgene ---
def get_surprise_html():
    m = st.session_state.mode
    if m == "GIF":
        return f'<div style="text-align:center"><img src="{st.session_state.gif}" width="200"/></div>'
    elif m == "Image":
        return f'<div style="text-align:center"><img src="{st.session_state.img}" width="200"/></div>'
    else:
        return f'<div style="font-family:monospace; text-align:center; color:#5FAA58; margin:16px 0;">{st.session_state.banner}</div>'

# --- Motivasjonsmeldinger ---
MOTIVATION = {
    25: ["💥 God start! Du er ¼ på vei!", "🚀 25% allerede – imponerende!"],
    50: ["🏆 Halveis! Stå på videre!", "⭐ 50% – du ruller inn!"],
    75: ["🔥 75% – nesten i mål!", "💪 ¾ gjort – fullfør det!"],
   100: ["🎉 WOW – oppgave fullført!", "🥳 Fantastisk jobb – oppgave slaktet!"],
}

# --- Callback slider ---
def on_slider_change(task_id):
    task = next((t for t in st.session_state.tasks if t["id"] == task_id), None)
    if not task:
        return
    new_val = st.session_state[f"progress_{task_id}"]
    if new_val != task["progress"]:
        task["progress"] = new_val
        save_tasks()
        if new_val in MOTIVATION:
            st.success(random.choice(MOTIVATION[new_val]))
        if new_val == 100:
            st.session_state.completed_count += 1
            save_stats()
            st.balloons()
            st.markdown(get_surprise_html(), unsafe_allow_html=True)
            # samle marquee-emoji hvis hver femte
            if st.session_state.completed_count % 5 == 0:
                st.session_state._celebrate_marquee = st.session_state.marquee

# --- Header & KPI ---
st.title("✅ Mine oppgaver")
c1, c2 = st.columns(2)
c1.metric("Oppgaver totalt", len(st.session_state.tasks))
c2.metric("Oppgaver fullført", st.session_state.completed_count)
st.markdown("---")

# --- Legg til ny oppgave (øverst!) ---
with st.expander("➕ Legg til ny oppgave", expanded=True):
    with st.form("new_task", clear_on_submit=True):
        title    = st.text_input("Tittel")
        desc     = st.text_area("Beskrivelse")
        wait_for = st.text_input("Kommentar: Hva venter du på?")
        ok       = st.form_submit_button("Legg til oppgave")
        if ok:
            if not title:
                st.error("❌ Tittel kan ikke være tom.")
            elif len(st.session_state.tasks) >= 10:
                st.error("❌ Maks 10 oppgaver tillatt.")
            else:
                nt = {
                    "id":       str(uuid.uuid4()),
                    "title":    title,
                    "desc":     desc,
                    "wait_for": wait_for.strip(),
                    "progress": 0
                }
                st.session_state.tasks.append(nt)
                save_tasks()
                st.success("🚀 Ny oppgave registrert!")
st.markdown("---")

# --- Pågående oppgaver ---
st.markdown("🔍 **Pågående oppgaver**")
celebrations = []
to_remove    = []
for t in st.session_state.tasks:
    pct = t.get("progress", 0)
    emo = " 🙉" if t.get("wait_for") else ""
    hdr = f"{t['title']} — {pct}%{emo}"
    tid = t["id"]
    with st.expander(hdr, expanded=True):
        st.write(t.get("desc",""))
        if t.get("wait_for"):
            st.warning(f"Venter på: {t['wait_for']}")
        st.slider(
            "Fremdrift (%)", 0,100,
            value=pct, key=f"progress_{tid}",
            on_change=on_slider_change, args=(tid,)
        )
        # 90’s style bar
        st.markdown(f"""
          <div style="background:#222;border:2px solid #5FAA58;
                      border-radius:4px;height:24px;position:relative;">
            <div style="background:#5FAA58;width:{pct}%;height:100%;
                        transform:skew(-10deg);
                        box-shadow:0 0 8px #5FAA58,inset 0 0 4px #80c372;"></div>
            <div style="position:absolute;top:0;left:0;width:100%;
                        text-align:center;line-height:24px;
                        font-family:'Press Start 2P',monospace;
                        color:#FFF;font-size:12px;">{pct}%</div>
          </div>
        """, unsafe_allow_html=True)
        if pct == 100:
            to_remove.append(tid)
            # hente eventuelt marquee
            if hasattr(st.session_state, '_celebrate_marquee'):
                celebrations.append(st.session_state._celebrate_marquee)
                del st.session_state._celebrate_marquee

# fjern ferdige oppgaver
for tid in to_remove:
    st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != tid]
save_tasks()

# vis marquee-feiringer etter fjerning
for em in celebrations:
    st.success(f"✨ Du har fullført {st.session_state.completed_count} oppgaver! ✨")
    st.markdown(
        f"""
        <marquee behavior="smooth" direction="left" scrollamount="15">
          <span style="font-size:48px;">{em}</span>
        </marquee>
        """, unsafe_allow_html=True
    )

st.markdown("---")
# --- Innstillinger (collapsed default) ---
with st.expander("⚙️ Innstillinger overraskelse", expanded=False):
    mode = st.radio("Vis overraskelse som:", ["GIF","Image","CSS"],
                    index=["GIF","Image","CSS"].index(st.session_state.mode))
    st.session_state.mode = mode

    st.text_input("GIF-URL",     st.session_state.gif,    key="gif")
    st.text_input("Image-URL",   st.session_state.img,    key="img")
    st.text_area("Banner-tekst", st.session_state.banner,key="banner", height=80)
    st.text_input("Marquee-emoji", st.session_state.marquee, key="marquee")

    save_settings()
