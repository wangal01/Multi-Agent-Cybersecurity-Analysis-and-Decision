const $ = (id) => document.getElementById(id);

const EVENT_LABELS = {
  info: "系统",
  tool_start: "工具",
  assistant_call: "子智能体",
  session_created: "会话",
  task_result: "完成",
  error: "错误",
};

const EVENT_AVATAR = {
  info: "info",
  tool_start: "tool",
  assistant_call: "agent",
  session_created: "ok",
  task_result: "ok",
  error: "err",
};

let ws = null;
let sessionPath = null;

function getThreadId() {
  let id = $("threadId").value.trim();
  if (!id) {
    id = "session-" + Date.now().toString(36);
    $("threadId").value = id;
  }
  return id;
}

function wsUrl(threadId) {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return proto + "//" + location.host + "/ws/" + encodeURIComponent(threadId);
}

function scrollChatToBottom() {
  const feed = $("chatFeed");
  feed.scrollTop = feed.scrollHeight;
}

function hideEmptyState() {
  const el = $("emptyState");
  if (el) el.classList.add("hidden");
}

function formatTime(timestamp) {
  return timestamp
    ? new Date(timestamp).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function appendChatBubble(role, text, badgeLabel, timestamp) {
  hideEmptyState();
  const feed = $("chatFeed");
  const time = formatTime(timestamp);

  const msg = document.createElement("div");
  msg.className = "msg msg-" + role;

  const av = document.createElement("div");
  av.className = "msg-avatar " + (role === "user" ? "user" : "bot");
  av.textContent = role === "user" ? "我" : "AI";
  msg.appendChild(av);

  const body = document.createElement("div");
  body.className = "msg-body";
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  const meta = document.createElement("div");
  meta.className = "msg-meta";
  meta.innerHTML =
    '<span class="msg-time">' + time + '</span><span class="msg-badge">' + badgeLabel + "</span>";
  bubble.appendChild(meta);

  const textEl = document.createElement("div");
  textEl.className = "msg-text";
  textEl.textContent = text;
  bubble.appendChild(textEl);

  body.appendChild(bubble);
  msg.appendChild(body);
  feed.appendChild(msg);
  scrollChatToBottom();
}

function appendUserMessage(text) {
  appendChatBubble("user", text, "你的提问");
}

function appendAssistantMessage(text, timestamp) {
  appendChatBubble("assistant", text, "助手回复", timestamp);
}

function appendLog(event, message, data, timestamp) {
  hideEmptyState();
  const feed = $("chatFeed");
  const time = formatTime(timestamp);
  const label = EVENT_LABELS[event] || event;
  const avatarClass = EVENT_AVATAR[event] || "info";
  const isSystem = event === "info";

  const msg = document.createElement("div");
  msg.className = "msg " + (isSystem ? "msg-system" : "msg-event " + event);

  if (!isSystem) {
    const av = document.createElement("div");
    av.className = "msg-avatar " + avatarClass;
    av.textContent = label.charAt(0);
    msg.appendChild(av);
  }

  const body = document.createElement("div");
  body.className = "msg-body";
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  if (!isSystem) {
    const meta = document.createElement("div");
    meta.className = "msg-meta";
    meta.innerHTML =
      '<span class="msg-time">' + time + '</span><span class="msg-badge">' + label + "</span>";
    bubble.appendChild(meta);
  } else {
    const meta = document.createElement("span");
    meta.className = "msg-time";
    meta.textContent = time + " · ";
    bubble.appendChild(meta);
  }

  const text = document.createElement("div");
  text.className = "msg-text";
  text.textContent = message;
  bubble.appendChild(text);

  if (data && Object.keys(data).length > 0 && event !== "task_result") {
    const pre = document.createElement("pre");
    pre.className = "msg-json";
    pre.textContent = JSON.stringify(data, null, 2);
    bubble.appendChild(pre);
  }

  body.appendChild(bubble);
  msg.appendChild(body);
  feed.appendChild(msg);
  scrollChatToBottom();
}

function setWsState(connected, running) {
  const pill = $("statusPill");
  $("wsDot").className = "dot" + (running ? " running" : connected ? " connected" : "");
  if (connected) {
    pill.classList.add("connected");
    $("wsStatus").textContent = running ? "处理中…" : "已连接";
  } else {
    pill.classList.remove("connected");
    $("wsStatus").textContent = running ? "连接中…" : "未连接";
  }
  $("btnStart").disabled = !connected;
  $("btnUpload").disabled = !connected;
  $("btnListFiles").disabled = !sessionPath;
}

function connectWs() {
  const threadId = getThreadId();
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();
  ws = new WebSocket(wsUrl(threadId));
  setWsState(false, true);
  $("wsStatus").textContent = "连接中…";

  ws.onopen = () => {
    setWsState(true, false);
    $("wsStatus").textContent = threadId.slice(0, 12) + (threadId.length > 12 ? "…" : "");
    appendLog("info", "WebSocket 已连接");
    ws.send("ping");
  };

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "pong") return;
      if (msg.type !== "monitor_event") return;
      const { event, message, data, timestamp } = msg;

      if (event === "task_result" && data && data.result) {
        appendAssistantMessage(data.result, timestamp);
        appendLog("info", "本轮任务已完成", null, timestamp);
        setWsState(true, false);
        return;
      }

      appendLog(event, message, data, timestamp);
      if (event === "session_created" && data && data.path) {
        sessionPath = data.path;
        $("btnListFiles").disabled = false;
      }
      if (event === "tool_start" || event === "assistant_call") setWsState(true, true);
      if (event === "error") setWsState(true, false);
    } catch (e) {
      appendLog("info", String(ev.data));
    }
  };

  ws.onclose = () => {
    setWsState(false, false);
    $("wsStatus").textContent = "未连接";
    appendLog("info", "连接已断开");
  };

  ws.onerror = () => {
    setWsState(false, false);
    $("wsStatus").textContent = "连接失败";
  };
}

async function startTask() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    alert("请先点击左侧「连接」");
    return;
  }
  const query = $("query").value.trim();
  if (!query) {
    alert("请输入问题");
    return;
  }

  appendUserMessage(query);
  $("query").value = "";

  setWsState(true, true);
  appendLog("info", "正在发送…");

  const thread_id = getThreadId();
  const res = await fetch("/api/task", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, thread_id }),
  });
  const data = await res.json();
  if (!res.ok) {
    appendLog("error", "提交失败", data);
    setWsState(true, false);
    return;
  }
  appendLog("info", "已提交，Agent 开始处理");
}

async function uploadFiles() {
  const files = $("fileInput").files;
  if (!files.length) {
    $("uploadHint").textContent = "请先选择文件";
    return;
  }
  const fd = new FormData();
  for (let i = 0; i < files.length; i++) fd.append("files", files[i]);
  fd.append("thread_id", getThreadId());
  $("uploadHint").textContent = "上传中…";
  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const data = await res.json();
  $("uploadHint").textContent = res.ok ? "已上传: " + (data.files || []).join(", ") : "上传失败";
}

async function listOutputFiles() {
  if (!sessionPath) {
    alert("等待任务创建会话目录后再试");
    return;
  }
  const res = await fetch("/api/files?path=" + encodeURIComponent(sessionPath));
  const data = await res.json();
  const list = $("filesList");
  list.innerHTML = "";
  if (data.error) {
    list.textContent = data.error;
    return;
  }
  if (!data.files || !data.files.length) {
    list.textContent = "暂无生成文件";
    return;
  }
  data.files.forEach((f) => {
    const a = document.createElement("a");
    a.href = "/api/download?path=" + encodeURIComponent(f.path);
    a.textContent = f.name + " (" + (f.size / 1024).toFixed(1) + " KB)";
    a.download = f.name;
    list.appendChild(a);
  });
}

function resetEmptyState() {
  $("chatFeed").innerHTML =
    '<div class="empty-state" id="emptyState">' +
    '<div class="empty-icon" aria-hidden="true">\u25C7</div>' +
    "<p>\u8fde\u63a5\u4f1a\u8bdd\u540e\uff0c\u5728\u6b64\u67e5\u770b\u5bf9\u8bdd\u4e0e Agent \u6267\u884c\u8fdb\u5ea6</p></div>";
}

function initUi() {
  document.title = "\u4f01\u4e1a\u5b89\u5168\u52a9\u624b \u00b7 Deep Search Pro";
  $("subtitle").textContent =
    "\u6f0f\u6d1e\u60c5\u62a5 \u00b7 \u5408\u89c4\u6cd5\u5f8b \u00b7 \u5185\u90e8\u8d44\u4ea7\u95ee\u7b54";
  $("query").value = "";
  $("query").placeholder = "\u8f93\u5165\u5b89\u5168\u95ee\u9898\u2026";

  document.querySelectorAll(".chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      $("query").value = btn.getAttribute("data-q") || "";
      $("query").focus();
    });
  });

  $("query").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!$("btnStart").disabled) startTask();
    }
  });
}

$("btnConnect").addEventListener("click", connectWs);
$("btnStart").addEventListener("click", startTask);
$("btnUpload").addEventListener("click", uploadFiles);
$("btnListFiles").addEventListener("click", listOutputFiles);
$("btnClearLog").addEventListener("click", () => {
  resetEmptyState();
  sessionPath = null;
  $("btnListFiles").disabled = true;
});
$("btnNewSession").addEventListener("click", () => {
  if (ws) ws.close();
  $("threadId").value = "session-" + Date.now().toString(36);
  resetEmptyState();
  sessionPath = null;
  $("filesList").innerHTML = "";
  $("btnListFiles").disabled = true;
  setWsState(false, false);
  $("wsStatus").textContent = "未连接";
});
$("threadId").addEventListener("change", () => {
  if (ws) ws.close();
  setWsState(false, false);
});

initUi();
