# -*- coding: utf-8 -*-
"""
ProtocoLayer
============
高校「情報Ⅰ」向け教材アプリ。
メール送信を題材に、TCP/IPの4階層モデルにおける
「カプセル化」と「デカプセル化」を体験的に学習できる。

・外部データベース、Socket通信は一切使用しない。
・すべての通信は st.session_state を用いた疑似表現である。
・実装は教材としての可読性を最優先する。
"""

import html
import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# 定数定義（保守しやすいように一箇所にまとめる）
# ============================================================

APP_TITLE = "📮 ProtocoLayer"
APP_SUBTITLE = "メールを送ってTCP/IPの階層構造を学ぼう"

LEARNING_GOALS = [
    "通信プロトコルとは「通信の約束事」であること",
    "TCP/IPでは階層ごとに役割が分かれていること",
    "送信側ではデータにヘッダを付けながら下位層へ渡す（カプセル化）",
    "受信側ではヘッダを取り除きながら上位層へ渡す（デカプセル化）",
    "送信と受信では処理の流れが逆になること",
    "メールが相手へ届くまでの流れをイメージできること",
]

# 初期値（生徒が変更できる）
DEFAULT_SUBJECT = "文化祭のご案内"
DEFAULT_BODY = "来週の文化祭にぜひお越しください。"
DEFAULT_SENDER_IP = "192.168.1.10"
DEFAULT_RECEIVER_IP = "203.0.113.25"
DEFAULT_SENDER_MAC = "AA:BB:CC:11:22:33"
DEFAULT_RECEIVER_MAC = "44:55:66:77:88:99"
DEFAULT_SENDER_PORT = 52134
DEFAULT_RECEIVER_PORT = 25
TTL_VALUE = 64  # TTLは固定

# 階層ごとの色（カプセル化表示の色分け）
LAYER_COLOR = {
    "app": "#2563EB",       # アプリケーション層：青
    "tcp": "#16A34A",       # トランスポート層：緑
    "ip": "#F97316",        # インターネット層：オレンジ
    "ethernet": "#DC2626",  # ネットワークインターフェース層：赤
}
LAYER_BG = {
    "app": "#DBEAFE",
    "tcp": "#DCFCE7",
    "ip": "#FFEDD5",
    "ethernet": "#FEE2E2",
}

# 階層の正式名称
LAYER_LABEL = {
    "app": "アプリケーション層（SMTP）",
    "tcp": "トランスポート層（TCP）",
    "ip": "インターネット層（IP）",
    "ethernet": "ネットワークインターフェース層（Ethernet）",
}

# クイズの選択肢と各層の正解
QUIZ_OPTIONS = ["TCP", "IP", "SMTP", "Ethernet"]
QUIZ_ANSWER = {
    "app": "SMTP",
    "tcp": "TCP",
    "ip": "IP",
    "ethernet": "Ethernet",
}
QUIZ_LAYER_JP = {
    "app": "アプリケーション",
    "tcp": "トランスポート",
    "ip": "インターネット",
    "ethernet": "ネットワークインターフェース",
}

STEP_MAX = 10

# 各STEPのタイトルと、そのSTEPで強調する階層／通信経路上の位置
STEP_INFO = {
    1: {"title": "STEP1　メール作成", "layer": None, "path": "sender"},
    2: {"title": "STEP2　アプリケーション層", "layer": "app", "path": "sender"},
    3: {"title": "STEP3　トランスポート層", "layer": "tcp", "path": "sender"},
    4: {"title": "STEP4　インターネット層", "layer": "ip", "path": "sender"},
    5: {"title": "STEP5　ネットワークインターフェース層", "layer": "ethernet", "path": "sender"},
    6: {"title": "STEP6　インターネット通過", "layer": None, "path": "internet"},
    7: {"title": "STEP7　ネットワークインターフェース層 除去", "layer": "ethernet", "path": "receiver"},
    8: {"title": "STEP8　インターネット層 除去", "layer": "ip", "path": "receiver"},
    9: {"title": "STEP9　トランスポート層 除去", "layer": "tcp", "path": "receiver"},
    10: {"title": "STEP10　メール表示", "layer": "app", "path": "receiver"},
}

# 各階層で表示する説明文（教師モード等で使用）
STEP_MESSAGE = {
    "app": "メールとして送れる形を作ります。",
    "tcp": "どのアプリへ届けるかを決めます。",
    "ip": "相手のネットワークまで運びます。",
    "ethernet": "LAN内で届けるための情報を付けます。",
}


# ============================================================
# セッション状態の初期化・リセット
# ============================================================

def init_session_state():
    """アプリ起動時に一度だけ、必要な状態を初期化する。"""
    defaults = {
        "mode": "pair",              # "pair"（ペア体験） or "single"（ステップ実行）
        "step": 1,                   # 現在のステップ（1〜10）
        "show_final": False,         # 最終画面を表示するか
        "teacher_mode": False,       # 教師モードON/OFF
        "show_explanation": True,    # 解説表示ON/OFF
        "subject": DEFAULT_SUBJECT,
        "message": DEFAULT_BODY,
        "sender_ip": DEFAULT_SENDER_IP,
        "receiver_ip": DEFAULT_RECEIVER_IP,
        "sender_mac": DEFAULT_SENDER_MAC,
        "receiver_mac": DEFAULT_RECEIVER_MAC,
        "sender_port": DEFAULT_SENDER_PORT,
        "receiver_port": DEFAULT_RECEIVER_PORT,
        "ttl": TTL_VALUE,
        # packet_layers: 内側から外側への順。カプセル化が進むほど要素が増える。
        "packet_layers": ["app"],
        "received_packet": None,     # ペアモードで「送信」された時点のパケット
        "quiz_result": {},           # 各層のクイズ正誤 {"app": True, ...}
        "quiz_choice": {},           # 各層で選んだ選択肢
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_progress():
    """学習の進み具合（ステップやパケット状態）だけをリセットする。
    件名・本文・IPなどの入力値やモード設定は維持しない（最初からやり直す）。
    """
    st.session_state.step = 1
    st.session_state.show_final = False
    st.session_state.packet_layers = ["app"]
    st.session_state.received_packet = None
    st.session_state.quiz_result = {}
    st.session_state.quiz_choice = {}
    st.session_state.subject = DEFAULT_SUBJECT
    st.session_state.message = DEFAULT_BODY
    st.session_state.sender_ip = DEFAULT_SENDER_IP
    st.session_state.receiver_ip = DEFAULT_RECEIVER_IP
    st.session_state.sender_mac = DEFAULT_SENDER_MAC
    st.session_state.receiver_mac = DEFAULT_RECEIVER_MAC
    st.session_state.sender_port = DEFAULT_SENDER_PORT
    st.session_state.receiver_port = DEFAULT_RECEIVER_PORT


# ============================================================
# 画面スクロール制御
# ============================================================
# Streamlitは通常、再描画（rerun）してもスクロール位置を保持したままになる。
# 「次へ」等のボタンでステップが進んだときは、生徒が画面上部
# （通信経路やタイトルなど）を毎回見られるよう、自動でページ上部へ
# スクロールさせる。

def request_scroll_to_top():
    """次の再描画時にページ上部へスクロールするよう予約する。
    ステップを進めるボタンの処理（st.rerun()の直前）で呼び出す。
    """
    st.session_state["_scroll_to_top"] = True


def scroll_to_top():
    """ページ上部（Streamlitのメインコンテナ）までスクロールする。
    高さ0の非表示コンポーネントとしてJavaScriptを埋め込むことで実現する。
    """
    components.html(
        """
        <script>
            setTimeout(function () {
                var container = window.parent.document.querySelector(
                    'section.main div[data-testid="stAppViewContainer"]'
                ) || window.parent.document.querySelector('section.main');
                if (container) {
                    container.scrollTo({ top: 0, behavior: "auto" });
                }
                window.parent.scrollTo({ top: 0, behavior: "auto" });
            }, 30);
        </script>
        """,
        height=0,
    )


# ============================================================
# サイドバー
# ============================================================

def render_sidebar():
    """モード切り替え・リセット・教師モード・解説表示のUIを描画する。"""
    with st.sidebar:
        st.header("⚙️ 設定")

        mode_label = st.radio(
            "学習モードを選んでください",
            options=["pair", "single"],
            format_func=lambda m: "👫 ペア体験モード" if m == "pair" else "🚶 ステップ実行モード",
            index=0 if st.session_state.mode == "pair" else 1,
        )
        if mode_label != st.session_state.mode:
            st.session_state.mode = mode_label
            reset_progress()
            request_scroll_to_top()
            st.rerun()

        st.divider()

        st.session_state.teacher_mode = st.toggle(
            "🧑‍🏫 教師モード", value=st.session_state.teacher_mode,
            help="ONにするとクイズの正解があらかじめ選ばれ、確認なしで先へ進めます。"
        )
        st.session_state.show_explanation = st.toggle(
            "💡 各階層の解説を表示", value=st.session_state.show_explanation
        )

        st.divider()

        if st.button("🔄 最初からやり直す", use_container_width=True):
            reset_progress()
            request_scroll_to_top()
            st.rerun()

        st.divider()
        st.caption("ProtocoLayer は疑似通信教材です。実際の通信は行いません。")


# ============================================================
# ヘッダー（タイトル・学習目標・現在のステップ）
# ============================================================

def render_header():
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    with st.expander("🎯 この教材の学習目標", expanded=False):
        for goal in LEARNING_GOALS:
            st.markdown(f"- {goal}")

    info = STEP_INFO[st.session_state.step]
    progress_ratio = st.session_state.step / STEP_MAX
    st.progress(progress_ratio, text=f"現在のステップ： {info['title']}")


# ============================================================
# 通信経路のイラスト表示
# ============================================================

def render_communication_path():
    """送信者PC → LAN → ルータ → インターネット → ルータ → LAN → 受信者PC
    を横に並べたイラストを表示する。現在のステップに応じて該当区間を強調する。
    インターネット区間は常に色を変えて表示する。
    """
    active_path = STEP_INFO[st.session_state.step]["path"]

    nodes = [
        ("💻 送信者PC", "sender"),
        ("🔌 LAN", "sender"),
        ("📡 ルータ", "sender"),
        ("🌐 インターネット", "internet"),
        ("📡 ルータ", "receiver"),
        ("🔌 LAN", "receiver"),
        ("💻 受信者PC", "receiver"),
    ]

    boxes_html = []
    for i, (label, owner) in enumerate(nodes):
        is_internet = owner == "internet"
        is_active = (owner == active_path)

        if is_internet:
            bg = "#7C3AED"       # インターネットは常に紫で目立たせる
            text_color = "#FFFFFF"
            border = "3px solid #4C1D95"
        elif is_active:
            bg = "#FEF08A"       # 現在アクティブな区間は黄色で強調
            text_color = "#111827"
            border = "3px solid #CA8A04"
        else:
            bg = "#F3F4F6"
            text_color = "#374151"
            border = "2px solid #D1D5DB"

        box = f"""
        <div style="background:{bg};color:{text_color};border:{border};
                    border-radius:10px;padding:8px 6px;text-align:center;
                    font-size:13px;font-weight:600;min-width:90px;">
            {label}
        </div>
        """
        boxes_html.append(box)
        if i != len(nodes) - 1:
            boxes_html.append(
                '<div style="font-size:20px;color:#9CA3AF;">→</div>'
            )

    path_html = f"""
    <div style="display:flex;align-items:center;justify-content:center;
                gap:6px;flex-wrap:wrap;padding:12px 0;">
        {''.join(boxes_html)}
    </div>
    """
    st.markdown(path_html, unsafe_allow_html=True)


# ============================================================
# パケット構造（カプセル化）の表示
# ============================================================

def render_packet_box(layers):
    """packet_layers（内側から外側の順）を受け取り、
    封筒に包まれるようにネストしたHTMLを組み立てて表示する。
    """
    # ユーザー入力はHTMLとして解釈されないようエスケープしてから埋め込む
    safe_subject = html.escape(st.session_state.subject)
    safe_message = html.escape(st.session_state.message).replace("\n", "<br>")

    # 一番内側（メール本体）から順にHTMLを組み立てる
    inner_html = f"""
    <div style="background:#FFFFFF;border:2px dashed #93C5FD;border-radius:8px;
                padding:10px;font-size:13px;color:#1E3A8A;">
        ✉️ 件名：{safe_subject}<br>
        本文：{safe_message}
    </div>
    """

    # まずメール本体（app）を中心に置き、それ以外の層を外側から順に包む
    content = inner_html
    for layer in layers:
        if layer == "app":
            content = f"""
            <div style="background:{LAYER_BG['app']};border:2px solid {LAYER_COLOR['app']};
                        border-radius:10px;padding:10px;">
                <div style="font-size:12px;font-weight:700;color:{LAYER_COLOR['app']};margin-bottom:4px;">
                    ✉️ メール（アプリケーション層）
                </div>
                {content}
            </div>
            """
        elif layer == "tcp":
            content = f"""
            <div style="background:{LAYER_BG['tcp']};border:2px solid {LAYER_COLOR['tcp']};
                        border-radius:10px;padding:10px;">
                <div style="font-size:12px;font-weight:700;color:{LAYER_COLOR['tcp']};margin-bottom:4px;">
                    🟩 TCPヘッダ（送信元Port:{html.escape(str(st.session_state.sender_port))} / 宛先Port:{html.escape(str(st.session_state.receiver_port))}）
                </div>
                {content}
            </div>
            """
        elif layer == "ip":
            content = f"""
            <div style="background:{LAYER_BG['ip']};border:2px solid {LAYER_COLOR['ip']};
                        border-radius:10px;padding:10px;">
                <div style="font-size:12px;font-weight:700;color:{LAYER_COLOR['ip']};margin-bottom:4px;">
                    🟧 IPヘッダ（送信元IP:{html.escape(st.session_state.sender_ip)} / 宛先IP:{html.escape(st.session_state.receiver_ip)} / TTL:{st.session_state.ttl}）
                </div>
                {content}
            </div>
            """
        elif layer == "ethernet":
            content = f"""
            <div style="background:{LAYER_BG['ethernet']};border:2px solid {LAYER_COLOR['ethernet']};
                        border-radius:10px;padding:10px;">
                <div style="font-size:12px;font-weight:700;color:{LAYER_COLOR['ethernet']};margin-bottom:4px;">
                    🟥 Ethernetヘッダ（送信元MAC:{html.escape(st.session_state.sender_mac)} / 宛先MAC:{html.escape(st.session_state.receiver_mac)}）
                </div>
                {content}
            </div>
            """

    st.markdown(
        f'<div style="max-width:520px;margin:0 auto;">{content}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# クイズ機能
# ============================================================

def render_quiz(layer_key, key_suffix=""):
    """指定した階層のクイズを表示し、正解しているかどうかを返す。
    教師モードONの場合は正解を自動選択し、常に正解扱いとする。
    """
    correct = QUIZ_ANSWER[layer_key]
    quiz_key = f"quiz_{layer_key}{key_suffix}"

    st.markdown(f"**❓ この階層で追加するヘッダはどれ？**")

    if st.session_state.teacher_mode:
        # 教師モード：正解があらかじめ選ばれた状態にし、常に通過できる
        default_index = QUIZ_OPTIONS.index(correct)
        choice = st.radio(
            "選択肢", QUIZ_OPTIONS, index=default_index,
            key=quiz_key, horizontal=True,
        )
        st.info("🧑‍🏫 教師モード：正解が選択済みです。そのまま次へ進めます。")
        st.session_state.quiz_result[layer_key] = True
        return True

    choice = st.radio(
        "選択肢", QUIZ_OPTIONS, index=None,
        key=quiz_key, horizontal=True,
    )

    if choice is None:
        st.session_state.quiz_result[layer_key] = False
        return False

    if choice == correct:
        st.success(f"✅ 正しい！この階層では{correct}を追加します。")
        st.session_state.quiz_result[layer_key] = True
        return True
    else:
        jp_name = QUIZ_LAYER_JP[layer_key]
        st.error(f"❌ 違います。{jp_name}層では{correct}を追加します。")
        st.session_state.quiz_result[layer_key] = False
        return False


# ============================================================
# 送信者・受信者 入力パネル
# ============================================================

def render_sender_inputs():
    """送信者側の入力項目（件名・本文・IP・MAC・ポート）を描画する。"""
    st.subheader("📤 送信者")
    st.session_state.subject = st.text_input("件名", st.session_state.subject)
    st.session_state.message = st.text_area("本文", st.session_state.message, height=80)

    with st.expander("🔧 詳細設定（IP / MAC / ポート）", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.sender_ip = st.text_input("送信元IP", st.session_state.sender_ip)
            st.session_state.sender_mac = st.text_input("送信元MAC", st.session_state.sender_mac)
            st.session_state.sender_port = st.number_input(
                "送信元ポート", value=int(st.session_state.sender_port), step=1
            )
        with col2:
            st.session_state.receiver_ip = st.text_input("宛先IP", st.session_state.receiver_ip)
            st.session_state.receiver_mac = st.text_input("宛先MAC", st.session_state.receiver_mac)
            st.session_state.receiver_port = st.number_input(
                "宛先ポート", value=int(st.session_state.receiver_port), step=1
            )


def render_receiver_panel(revealed_layers):
    """受信者側の状態表示（簡易）。詳細なパケット構造は画面下部にまとめて表示する。"""
    st.subheader("📥 受信者")
    if revealed_layers is None:
        st.info("まだ何も届いていません。送信を待っています…")
        return
    remaining = [l for l in revealed_layers if l != "app"]
    if remaining:
        names = "・".join(LAYER_LABEL[l].split("（")[0] for l in reversed(remaining))
        st.warning(f"📦 まだ外側に「{names}」が残っています。")
    else:
        st.success("✅ すべてのヘッダが外れ、メール本文が読める状態になりました！")


# ============================================================
# ステップごとの説明文
# ============================================================

def render_layer_explanation(layer_key):
    if not st.session_state.show_explanation or layer_key is None:
        return
    st.markdown(
        f"""
        <div style="background:#F0F9FF;border-left:5px solid #0284C7;
                    padding:10px 14px;border-radius:6px;margin-top:8px;">
            <b>{LAYER_LABEL[layer_key]}</b><br>{STEP_MESSAGE[layer_key]}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# ステップ実行モード
# ============================================================

def can_advance():
    """現在のステップから次に進んでよいかを判定する。
    クイズがある層（app, tcp, ip, ethernet を"追加"するステップ）は
    正解しないと進めない。
    """
    step = st.session_state.step
    info = STEP_INFO[step]
    layer = info["layer"]
    # STEP2〜5（追加）はクイズ必須。STEP7〜10（除去）はクイズなしで進める。
    if step in (2, 3, 4, 5):
        return st.session_state.quiz_result.get(layer, False)
    return True


def apply_step_effect(step):
    """ステップ番号に応じて packet_layers を更新する（副作用）。"""
    layers = st.session_state.packet_layers
    if step == 3 and "tcp" not in layers:
        layers.append("tcp")
    elif step == 4 and "ip" not in layers:
        layers.append("ip")
    elif step == 5 and "ethernet" not in layers:
        layers.append("ethernet")
    elif step == 7 and "ethernet" in layers:
        layers.remove("ethernet")
    elif step == 8 and "ip" in layers:
        layers.remove("ip")
    elif step == 9 and "tcp" in layers:
        layers.remove("tcp")
    st.session_state.packet_layers = layers


def render_single_mode():
    """ステップ実行モード（一人学習用）。「次へ」ボタンで1ステップずつ進む。"""
    step = st.session_state.step
    info = STEP_INFO[step]

    render_communication_path()
    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        if step == 1:
            render_sender_inputs()
        else:
            st.subheader("📤 送信者")
            st.caption(f"件名：{st.session_state.subject}")
    with col_right:
        if step >= 7:
            render_receiver_panel(st.session_state.packet_layers)
        else:
            st.subheader("📥 受信者")
            st.info("まだ受信していません。")

    st.divider()
    st.markdown("### 📦 現在のパケット構造")
    render_packet_box(st.session_state.packet_layers)

    if info["layer"]:
        render_layer_explanation(info["layer"])

    # クイズ（追加ステップのみ）
    if step in (2, 3, 4, 5):
        render_quiz(info["layer"])

    st.divider()
    disabled = not can_advance()
    label = "🎉 完了する" if step == STEP_MAX else "次へ ➡️"
    if st.button(label, type="primary", disabled=disabled, use_container_width=True):
        if step < STEP_MAX:
            apply_step_effect(step + 1)
            st.session_state.step += 1
        else:
            st.session_state.show_final = True
        request_scroll_to_top()
        st.rerun()

    if disabled and step in (2, 3, 4, 5):
        st.caption("👆 クイズに正解すると次へ進めます。")


# ============================================================
# ペア体験モード
# ============================================================

def render_pair_mode():
    """1台のPCを2人で交互に操作するモード。
    STEP1〜6は送信者側が操作し、STEP7〜10は受信者側が操作する。
    """
    step = st.session_state.step
    info = STEP_INFO[step]
    sender_active = step <= 6
    receiver_active = step >= 6

    render_communication_path()
    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        border_style = "border:3px solid #2563EB;border-radius:10px;padding:10px;" if sender_active else ""
        st.markdown(f'<div style="{border_style}">', unsafe_allow_html=True)
        if step == 1:
            render_sender_inputs()
        else:
            st.subheader("📤 送信者")
            st.caption(f"件名：{st.session_state.subject}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        border_style = "border:3px solid #16A34A;border-radius:10px;padding:10px;" if receiver_active else ""
        st.markdown(f'<div style="{border_style}">', unsafe_allow_html=True)
        if step < 6:
            st.subheader("📥 受信者")
            st.info("送信者からのメールを待っています…")
        elif step == 6:
            st.subheader("📥 受信者")
            st.warning("📨 パケットがインターネットを越えて届きました！「受信」を押して中身を確認しましょう。")
        else:
            render_receiver_panel(st.session_state.received_packet)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📦 現在のパケット構造")
    # 送信側の作業中（STEP1〜6）は送信者のパケットを、
    # 受信側の作業中（STEP7〜10）は受信者が持つパケットを表示する。
    if step <= 6:
        render_packet_box(st.session_state.packet_layers)
    else:
        render_packet_box(st.session_state.received_packet)

    if info["layer"]:
        render_layer_explanation(info["layer"])

    # クイズ（送信側の追加ステップのみ、左側に表示）
    if step in (2, 3, 4, 5):
        render_quiz(info["layer"], key_suffix="_pair")

    st.divider()

    # --- ナビゲーションボタン（左右で役割分担） ---
    nav_left, nav_right = st.columns(2)

    with nav_left:
        if step <= 5:
            disabled = (step in (2, 3, 4, 5)) and not can_advance()
            btn_label = "📨 送信する" if step == 5 else "次へ ➡️"
            if st.button(btn_label, type="primary", disabled=disabled,
                         use_container_width=True, key="sender_next"):
                if step == 5:
                    apply_step_effect(5)  # ethernet層を追加して確定
                    st.session_state.received_packet = list(st.session_state.packet_layers)
                    st.session_state.step = 6
                else:
                    apply_step_effect(step + 1)
                    st.session_state.step += 1
                request_scroll_to_top()
                st.rerun()
            if disabled:
                st.caption("👆 クイズに正解すると次へ進めます。")

    with nav_right:
        if step == 6:
            if st.button("📬 受信する", type="primary", use_container_width=True, key="receiver_recv"):
                st.session_state.step = 7
                request_scroll_to_top()
                st.rerun()
        elif 7 <= step <= 9:
            if st.button("次へ（ヘッダを取り外す）➡️", type="primary",
                         use_container_width=True, key="receiver_next"):
                # 受信済みパケットから該当層を取り除く
                layers = st.session_state.received_packet
                if step == 7 and "ethernet" in layers:
                    layers.remove("ethernet")
                elif step == 8 and "ip" in layers:
                    layers.remove("ip")
                elif step == 9 and "tcp" in layers:
                    layers.remove("tcp")
                st.session_state.received_packet = layers
                st.session_state.step += 1
                request_scroll_to_top()
                st.rerun()
        elif step == 10:
            if st.button("🎉 メールを読む", type="primary", use_container_width=True, key="receiver_final"):
                st.session_state.show_final = True
                request_scroll_to_top()
                st.rerun()


# ============================================================
# 最終画面
# ============================================================

def render_final_screen():
    st.balloons()
    st.markdown(
        """
        <div style="text-align:center;padding:24px;">
            <h1>🎉 通信成功！</h1>
            <p style="font-size:18px;">メールが送信者から受信者まで無事に届きました。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 今回学んだこと")
    check_items = [
        "プロトコルは通信の約束事",
        "TCP/IPでは役割分担されている",
        "送信側ではカプセル化",
        "受信側ではデカプセル化",
        "メールは階層を順番に通って届く",
    ]
    for item in check_items:
        st.markdown(f"✔ {item}")

    st.divider()
    if st.button("🔁 もう一度挑戦", type="primary", use_container_width=True):
        reset_progress()
        request_scroll_to_top()
        st.rerun()


# ============================================================
# メイン処理
# ============================================================

def main():
    st.set_page_config(
        page_title="ProtocoLayer",
        page_icon="📮",
        layout="wide",
    )

    init_session_state()

    # 直前の操作でスクロール予約がされていれば、ページ上部へスクロールする
    if st.session_state.pop("_scroll_to_top", False):
        scroll_to_top()

    render_sidebar()
    render_header()

    st.divider()

    if st.session_state.show_final:
        render_final_screen()
        return

    if st.session_state.mode == "pair":
        render_pair_mode()
    else:
        render_single_mode()


if __name__ == "__main__":
    main()