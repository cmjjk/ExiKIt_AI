"""Оформление в стиле Fulfillix: тёмный фон, фиолетовый градиент, стеклянные карточки.
Только внешний вид: логики приложения здесь нет."""
import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--bg:#04031A;--bg2:#0B0A2E;--violet:#7B5CFF;--lilac:#E9DDFF;--mint:#7EE8C8;--pink:#FF5FA2;--amber:#F2C879;
--muted:#B7B0D6;--ink:#1B1040;--grad:linear-gradient(135deg,#4361EE,#8A2FE0);--line:rgba(220,205,255,.2)}
html,body,[class*="css"],.stApp,.stMarkdown,button,input,textarea,label{font-family:'Manrope',system-ui,sans-serif!important}
.stApp{background:radial-gradient(900px 600px at 80% -10%,rgba(138,47,224,.45),transparent 60%),
radial-gradient(800px 600px at -10% 40%,rgba(67,97,238,.35),transparent 60%),
radial-gradient(700px 500px at 60% 110%,rgba(255,95,162,.18),transparent 60%),
linear-gradient(180deg,var(--bg),var(--bg2));background-attachment:fixed;color:#F3EEFF}
.stApp::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
background-size:56px 56px;-webkit-mask-image:radial-gradient(ellipse at 50% 30%,#000 20%,transparent 75%);mask-image:radial-gradient(ellipse at 50% 30%,#000 20%,transparent 75%)}
[data-testid="stHeader"]{background:transparent}
[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden}
.block-container{max-width:1100px;padding-top:2.2rem;position:relative;z-index:1}
h1,h2,h3,h4{font-family:'Unbounded','Manrope',sans-serif!important;font-weight:800!important;letter-spacing:-.01em;color:#F3EEFF!important}
h2,h3{font-size:1.15rem!important}
p,li,span,label{color:#E6DEFF}
[data-testid="stCaptionContainer"],small{color:var(--muted)!important}
a{color:var(--mint)!important}

/* nav-пилюля и герой */
.ek-nav{display:flex;align-items:center;gap:10px;background:rgba(236,228,255,.93);color:var(--ink);border-radius:22px;padding:10px 16px;
box-shadow:0 12px 40px -12px rgba(0,0,0,.6),inset 0 0 0 1px rgba(255,255,255,.7);font-family:'Unbounded',sans-serif;font-weight:800;font-size:15px;letter-spacing:.02em}
.ek-nav i{width:32px;height:32px;border-radius:10px;background:var(--grad);display:grid;place-items:center;color:#fff;font-style:normal;font-size:15px}
.ek-nav span.r{margin-left:auto;font-family:'Manrope',sans-serif;font-weight:700;font-size:13px;color:#4a3a8a}
.ek-chip{display:inline-flex;align-items:center;gap:8px;margin-top:34px;padding:8px 16px;border-radius:99px;background:rgba(255,255,255,.08);border:1px solid var(--line);font-size:14px;font-weight:600;color:#fff}
.ek-chip b{width:8px;height:8px;border-radius:50%;background:var(--mint);box-shadow:0 0 12px var(--mint);animation:ekpulse 2s infinite}
@keyframes ekpulse{50%{opacity:.35}}
[data-testid="stMarkdownContainer"] .ek-hero h1{font-size:clamp(34px,5.2vw,68px)!important;line-height:1!important;margin:20px 0 18px!important;letter-spacing:-.02em}
.ek-hero h1 .g{background:linear-gradient(90deg,#F4EBFF,#B9A2FF 60%,#7EE8C8);-webkit-background-clip:text;background-clip:text;color:transparent!important;filter:drop-shadow(0 0 22px rgba(170,140,255,.55))}
.ek-hero p{font-size:clamp(16px,1.4vw,19px);color:#D9D0F5;max-width:58ch;margin-bottom:26px}
.ek-eyebrow{font-family:'Unbounded',sans-serif;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--mint);margin:8px 0 4px}

/* стеклянные блоки */
[data-testid="stForm"],[data-testid="stFileUploader"] section,[data-testid="stAlert"],[data-testid="stExpander"],[data-testid="stJson"],
[data-testid="stTabs"] [role="tabpanel"]{background:linear-gradient(160deg,rgba(255,255,255,.1),rgba(255,255,255,.035));border:1px solid var(--line)!important;
border-radius:26px;backdrop-filter:blur(14px);box-shadow:inset 0 1px 0 rgba(255,255,255,.14),0 24px 50px -24px rgba(0,0,0,.7)}
[data-testid="stForm"]{padding:24px}
[data-testid="stFileUploaderDropzone"]{background:rgba(4,3,26,.45)!important;border:1.5px dashed rgba(220,205,255,.4)!important;border-radius:20px!important}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--violet)!important;background:rgba(123,92,255,.12)!important}
[data-testid="stFileUploaderDropzone"] *{color:#E6DEFF!important}
[data-testid="stAlert"]{border-radius:18px;padding:4px}
[data-testid="stTabs"] [role="tabpanel"]{padding:24px;margin-top:10px}

/* кнопки */
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondaryFormSubmit"],[data-testid="stBaseButton-primaryFormSubmit"]{
background:var(--grad)!important;color:#fff!important;border:0!important;border-radius:16px!important;font-weight:800!important;padding:.7rem 1.4rem!important;
box-shadow:4px 4px 0 var(--pink),0 12px 30px -8px rgba(123,92,255,.7)!important;transition:transform .2s,box-shadow .2s!important}
[data-testid="stBaseButton-primary"]:hover,[data-testid="stBaseButton-primaryFormSubmit"]:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--pink),0 16px 34px -8px rgba(123,92,255,.9)!important}
[data-testid="stBaseButton-primary"]:active,[data-testid="stBaseButton-primaryFormSubmit"]:active{transform:translate(3px,3px);box-shadow:1px 1px 0 var(--pink)!important}
[data-testid="stBaseButton-primary"]:disabled{opacity:.45;box-shadow:4px 4px 0 var(--pink)!important;transform:none}
[data-testid="stBaseButton-secondary"],[data-testid="stDownloadButton"] button{background:rgba(255,255,255,.07)!important;color:#fff!important;border:0!important;
border-radius:16px!important;font-weight:800!important;padding:.7rem 1.4rem!important;box-shadow:inset 0 0 0 1.5px rgba(220,205,255,.4)!important}
[data-testid="stBaseButton-secondary"]:hover,[data-testid="stDownloadButton"] button:hover{background:rgba(255,255,255,.14)!important}

/* поля */
input,textarea,[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div{background:rgba(4,3,26,.55)!important;color:#fff!important;border-radius:14px!important;border-color:var(--line)!important}
[data-baseweb="input"]:focus-within,[data-baseweb="base-input"]:focus-within{border-color:var(--violet)!important;box-shadow:0 0 0 3px rgba(123,92,255,.25)!important}

/* вкладки */
[role="tablist"]{gap:6px;background:rgba(255,255,255,.07);padding:4px!important;border-radius:14px;width:fit-content;border:0!important}
[role="tab"]{border-radius:10px!important;color:var(--muted)!important;font-weight:700!important;padding:8px 16px!important;height:auto!important;background:transparent!important}
[role="tab"] p,[role="tab"] span{color:inherit!important}
[role="tab"][aria-selected="true"]{background:var(--lilac)!important;color:var(--ink)!important}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none!important}

/* прогресс, сайдбар */
[data-testid="stProgress"] div[role="progressbar"]>div{background:linear-gradient(90deg,var(--mint),var(--violet))!important;border-radius:99px}
[data-testid="stProgress"] div[role="progressbar"]{background:rgba(255,255,255,.1)!important;border-radius:99px}
[data-testid="stSidebar"]{background:rgba(11,10,46,.85)!important;border-right:1px solid var(--line);backdrop-filter:blur(14px)}
[data-testid="stSidebar"] h3{font-size:.95rem!important}
code{background:rgba(255,255,255,.1)!important;color:var(--mint)!important;border-radius:8px}
hr{border-color:var(--line)!important}
[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2{color:var(--mint)!important;font-size:1rem!important;letter-spacing:.06em}
[data-testid="stMarkdownContainer"] h3{font-size:.95rem!important}
"""


def apply_theme():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def hero():
    st.markdown(
        """
<div class="ek-nav"><i>⎘</i>EXITKIT AI<span class="r">Open Source × AI</span></div>
<div class="ek-hero">
  <span class="ek-chip"><b></b>Работает локально через Ollama</span>
  <h1>Передайте <span class="g">дела за минуты</span>, а не за недели</h1>
  <p>Загрузите заметки и документы уходящего сотрудника, и ExitKit AI соберёт пакет передачи дел: проекты, задачи, сроки, риски, контакты и вопросы для уточнения.</p>
</div>
<div class="ek-eyebrow">Приложение</div>
""",
        unsafe_allow_html=True,
    )
