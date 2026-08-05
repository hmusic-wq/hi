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

# 各STEPのタイトルと、そのSTEPで強調する階層
STEP_INFO = {
    1: {"title": "STEP1 メール作成", "layer": None},
    2: {"title": "STEP2 アプリケーション層（データ準備）", "layer": "app"},
    3: {"title": "STEP3 トランスポート層（TCPヘッダ付加）", "layer": "tcp"},
    4: {"title": "STEP4 インターネット層（IPヘッダ付加）", "layer": "ip"},
    5: {"title": "STEP5 ネットワークインターフェース層（Ethernetヘッダ付加）", "layer": "ethernet"},
    6: {"title": "STEP6 インターネット通過", "layer": None},
    7: {"title": "STEP7 ネットワークインターフェース層 除去", "layer": "ethernet"},
    8: {"title": "STEP8 インターネット層 除去", "layer": "ip"},
    9: {"title": "STEP9 トランスポート層 除去", "layer": "tcp"},
    10: {"title": "STEP10 メール表示", "layer": "app"},
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
    入力値も初期値に戻す。
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

SCROLL_ANCHOR_ID = "protocolayer-top-anchor"


def request_scroll_to_top():
    """次の再描画時にページ上部へスクロールするよう予約する。"""
    st.session_state["_scroll_to_top"] = True


def scroll_to_top():
    """タイトル直前に置いたアンカー要素まで安全にスクロールする。
    iframe内クロスドメイン等でエラーが起きてもアプリがクラッシュしないようtry-catchで保護。
    """
    components.html(
        f"""
        <script>
            function scrollToAnchor() {{
                try {{
                    var doc = window.parent.document;
                    var anchor = doc.getElementById("{SCROLL_ANCHOR_ID}");
                    if (anchor) {{
                        anchor.scrollIntoView({{ behavior: "auto", block: "start" }});
                    }} else {{
                        window.parent.scrollTo({{ top: 0, behavior: "auto" }});
                    }}
                }} catch (e) {{
                    // クロスドメイン制約等で親Windowにアクセスできない場合の安全対策
                    window.scrollTo({{ top: 0, behavior: "auto" }});
                }}
            }}
            setTimeout(scrollToAnchor, 30);
            setTimeout(scrollToAnchor, 120);
            setTimeout(scrollToAnchor, 300);
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
    st.markdown(
        f'<div id="{SCROLL_ANCHOR_ID}" style="height:0;"></div>',
        unsafe_allow_html=True,
    )
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    with st.expander("🎯 この教材の学習目標", expanded=False):
        for goal in LEARNING_GOALS:
            st.markdown(f"- {goal}")

    info = STEP_INFO[st.session_state.step]
    progress_ratio = st.session_state.step / STEP_MAX
    st.progress(progress_ratio, text=f"現在のステップ： {info['title']}")


# ============================================================
# パケット構造（カプセル化）の表示
# ============================================================

LAYER_TAB_LABEL = {
    "app": "アプリケーション層",
    "tcp": "トランスポート層",
    "ip": "インターネット層",
    "ethernet": "ネットワークインターフェース層",
}


def _build_layer_box(layer_key, header_line_html, body_html=None):
    """1つの階層分を、独立した四角い箱として組み立てる。"""
    color = LAYER_COLOR[layer_key]
    bg = LAYER_BG[layer_key]
    tab_label = LAYER_TAB_LABEL[layer_key]
    body = f'<div style="margin-top:8px;">{body_html}</div>' if body_html else ""

    return f"""
    <div style="box-sizing:border-box;border:3px solid {color};border-radius:12px;
                background:{bg};overflow:hidden;">
        <div style="background:{color};color:#FFFFFF;font-size:11px;font-weight:800;
                    letter-spacing:1px;padding:4px 12px;">
            {tab_label}
        </div>
        <div style="box-sizing:border-box;padding:10px 14px;">
            <div style="font-size:12px;font-weight:700;color:{color};">
                {header_line_html}
            </div>
            {body}
        </div>
    </div>
    """


def render_packet_box(layers):
    """packet_layersを受け取り、視覚的に積み重ねて表示する。"""
    safe_subject = html.escape(st.session_state.subject)
    safe_message = html.escape(st.session_state.message).replace("
", "<br>")

    mail_body_html = f"""
    <div style="background:#FFFFFF;border:2px dashed #93C5FD;border-radius:8px;
                padding:10px;font-size:13px;color:#1E3A8A;">
        ✉️ 件名：{safe_subject}<br>
        本文：{safe_message}
    </div>
    """

    boxes_html = []
    for layer in reversed(layers):
        if layer == "app":
            header_line = "✉️ メールデータ（アプリケーション層データ）"
            boxes_html.append(_build_layer_box("app", header_line, mail_body_html))
        elif layer == "tcp":
            header_line = (
                f"🟩 TCPヘッダ（送信元Port:{html.escape(str(st.session_state.sender_port))} "
                f"/ 宛先Port:{html.escape(str(st.session_state.receiver_port))}）"
            )
            boxes_html.append(_build_layer_box("tcp", header_line))
        elif layer == "ip":
            header_line = (
                f"🟧 IPヘッダ（送信元IP:{html.escape(st.session_state.sender_ip)} "
                f"/ 宛先IP:{html.escape(st.session_state.receiver_ip)} "
                f"/ TTL:{st.session_state.ttl}）"
            )
            boxes_html.append(_build_layer_box("ip", header_line))
        elif layer == "ethernet":
            header_line = (
                f"🟥 Ethernetヘッダ（送信元MAC:{html.escape(st.session_state.sender_mac)} "
                f"/ 宛先MAC:{html.escape(st.session_state.receiver_mac)}）"
            )
            boxes_html.append(_build_layer_box("ethernet", header_line))

    stack_html = f"""
    <div style="max-width:480px;margin:0 auto;">
        <div style="text-align:center;font-size:12px;color:#6B7280;margin-bottom:4px;">
            ▲ 外側（あとから追加されたヘッダ）
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">
            {''.join(boxes_html)}
        </div>
        <div style="text-align:center;font-size:12px;color:#6B7280;margin-top:4px;">
            ▼ 内側（メール本体・データ）
        </div>
    </div>
    """
    st.markdown(stack_html, unsafe_allow_html=True)


# ============================================================
# クイズ機能
# ============================================================

def render_quiz(layer_key, key_suffix=""):
    """指定した階層のプロトコル確認クイズを表示し、正否を返す。"""
    correct = QUIZ_ANSWER[layer_key]
    quiz_key = f"quiz_{layer_key}{key_suffix}"

    if layer_key == "app":
        st.markdown(f"**❓ メール送受信で使われるアプリケーション層のプロトコルはどれ？**")
    else:
        st.markdown(f"**❓ この階層（{QUIZ_LAYER_JP[layer_key]}層）で扱う主要プロトコル/ヘッダはどれ？**")

    if st.session_state.teacher_mode:
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
        st.success(f"✅ 正解！この階層のプロトコルは {correct} です。")
        st.session_state.quiz_result[layer_key] = True
        return True
    else:
        jp_name = QUIZ_LAYER_JP[layer_key]
        st.error(f"❌ 違います。{jp_name}層のプロトコルは {correct} です。")
        st.session_state.quiz_result[layer_key] = False
        return False


# ============================================================
# 送信者・受信者 入力パネル
# ============================================================

def render_sender_inputs():
    """送信者側の入力項目（keyで直接session_stateに紐付け）。"""
    st.subheader("📤 送信者")
    st.text_input("件名", key="subject")
    st.text_area("本文", key="message", height=80)

    with st.expander("🔧 詳細設定（IP / MAC / ポート）", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("送信元IP", key="sender_ip")
            st.text_input("送信元MAC", key="sender_mac")
            st.number_input("送信元ポート", key="sender_port", step=1)
        with col2:
            st.text_input("宛先IP", key="receiver_ip")
            st.text_input("宛先MAC", key="receiver_mac")
            st.number_input("宛先ポート（メール受信用）", key="receiver_port", step=1)


def render_receiver_panel(revealed_layers):
    """受信者側の状態表示。"""
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
# ステップ実行モード
# ============================================================

def can_advance():
    """現在のステップから次に進んでよいかを判定する。"""
    step = st.session_state.step
    info = STEP_INFO[step]
    layer = info["layer"]
    if step in (2, 3, 4, 5):
        return st.session_state.quiz_result.get(layer, False)
    return True


def apply_step_effect(step):
    """ステップ番号に応じて packet_layers を更新する。"""
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
    """ステップ実行モード（一人学習用）。"""
    step = st.session_state.step
    info = STEP_INFO[step]

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

    # クイズ（追加ステップのみ）
    if step in (2, 3, 4, 5):
        render_quiz(info["layer"])

    st.divider()

    # ナビゲーション（前へ / 次へ）
    col_back, col_next = st.columns([1, 3])

    with col_back:
        if step > 1:
            if st.button("⬅️ 前へ", use_container_width=True):
                # 直前のステップに戻る際、追加された層を取り除く処理
                if step == 3 and "tcp" in st.session_state.packet_layers:
                    st.session_state.packet_layers.remove("tcp")
                elif step == 4 and "ip" in st.session_state.packet_layers:
                    st.session_state.packet_layers.remove("ip")
                elif step == 5 and "ethernet" in st.session_state.packet_layers:
                    st.session_state.packet_layers.remove("ethernet")
                elif step == 8 and "ethernet" not in st.session_state.packet_layers:
                    st.session_state.packet_layers.append("ethernet")
                elif step == 9 and "ip" not in st.session_state.packet_layers:
                    st.session_state.packet_layers.append("ip")
                elif step == 10 and "tcp" not in st.session_state.packet_layers:
                    st.session_state.packet_layers.append("tcp")

                st.session_state.step -= 1
                request_scroll_to_top()
                st.rerun()

    with col_next:
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
    """1台のPCを2人で交互に操作するモード。"""
    step = st.session_state.step
    info = STEP_INFO[step]
    sender_active = step <= 6
    receiver_active = step >= 6

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
    if step <= 6:
        render_packet_box(st.session_state.packet_layers)
    else:
        render_packet_box(st.session_state.received_packet)

    if step in (2, 3, 4, 5):
        render_quiz(info["layer"], key_suffix="_pair")

    st.divider()

    # --- ナビゲーションボタン ---
    nav_left, nav_right = st.columns(2)

    with nav_left:
        if step <= 5:
            disabled = (step in (2, 3, 4, 5)) and not can_advance()
            btn_label = "📨 送信する" if step == 5 else "次へ ➡️"
            
            c_back, c_next = st.columns([1, 2])
            with c_back:
                if step > 1:
                    if st.button("⬅️ 戻る", key="sender_back", use_container_width=True):
                        if step == 3 and "tcp" in st.session_state.packet_layers:
                            st.session_state.packet_layers.remove("tcp")
                        elif step == 4 and "ip" in st.session_state.packet_layers:
                            st.session_state.packet_layers.remove("ip")
                        elif step == 5 and "ethernet" in st.session_state.packet_layers:
                            st.session_state.packet_layers.remove("ethernet")
                        st.session_state.step -= 1
                        request_scroll_to_top()
                        st.rerun()

            with c_next:
                if st.button(btn_label, type="primary", disabled=disabled,
                             use_container_width=True, key="sender_next"):
                    if step == 5:
                        apply_step_effect(5)
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
            c_back, c_next = st.columns([1, 2])
            with c_back:
                if st.button("⬅️ 戻る", key="receiver_back", use_container_width=True):
                    layers = st.session_state.received_packet
                    if step == 8 and "ethernet" not in layers:
                        layers.append("ethernet")
                    elif step == 9 and "ip" not in layers:
                        layers.append("ip")
                    st.session_state.received_packet = layers
                    st.session_state.step -= 1
                    request_scroll_to_top()
                    st.rerun()

            with c_next:
                if st.button("次へ（ヘッダを取り外す）➡️", type="primary",
                             use_container_width=True, key="receiver_next"):
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
            c_back, c_next = st.columns([1, 2])
            with c_back:
                if st.button("⬅️ 戻る", key="receiver_back_10", use_container_width=True):
                    layers = st.session_state.received_packet
                    if "tcp" not in layers:
                        layers.append("tcp")
                    st.session_state.received_packet = layers
                    st.session_state.step -= 1
                    request_scroll_to_top()
                    st.rerun()
            with c_next:
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
        "送信側ではカプセル化（上位層→下位層へヘッダを付加）",
        "受信側ではデカプセル化（下位層→上位層へヘッダを除去）",
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

    render_sidebar()
    render_header()

    if st.session_state.pop("_scroll_to_top", False):
        scroll_to_top()

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
