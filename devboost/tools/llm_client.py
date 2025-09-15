import logging
import os
from typing import Any, ClassVar

import requests
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.config import get_config, set_config
from devboost.styles import get_status_style, get_tool_style

logger = logging.getLogger(__name__)


# ----------------------------- Provider Abstractions -----------------------------


class LLMProvider:
    """Abstract provider API.

    Concrete providers should implement list_models and chat.
    """

    name: str = ""

    def list_models(self) -> list[str]:
        raise NotImplementedError

    def chat(self, messages: list[dict[str, str]], model: str, params: dict[str, Any]) -> str:
        """Perform a chat completion and return assistant content as string.

        Default implementation provides a graceful fallback without network when
        no API key is available. Providers may override with real HTTP calls.
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    name = "OpenAI"

    # Static baseline list to avoid network calls in tests
    _models: ClassVar[list[str]] = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
        "o3-mini",
    ]

    def list_models(self) -> list[str]:
        return self._models

    def chat(self, messages: list[dict[str, str]], model: str, params: dict[str, Any]) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Offline-friendly deterministic response for tests
            return f"[OpenAI:{model}] (dry-run) You said: {messages[-1].get('content', '')}"
        # Minimal compatible call (OpenAI Responses API newer, but keep compat to Chat Completions)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(params.get("temperature", 0.7)),
            "max_tokens": int(params.get("max_tokens", 256)),
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


class AnthropicProvider(LLMProvider):
    name = "Anthropic"

    _models: ClassVar[list[str]] = [
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ]

    def list_models(self) -> list[str]:
        return self._models

    def chat(self, messages: list[dict[str, str]], model: str, params: dict[str, Any]) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return f"[Anthropic:{model}] (dry-run) You said: {messages[-1].get('content', '')}"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        # Convert OpenAI-like schema to Anthropic
        system = None
        user_messages: list[dict[str, str]] = []
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content")
            elif m.get("role") in ("user", "assistant"):
                # Anthropic expects an array of {role, content:[{type:"text", text:"..."}]}
                user_messages.append({
                    "role": m["role"],
                    "content": [{"type": "text", "text": m.get("content", "")}],
                })
        payload = {
            "model": model,
            "system": system,
            "messages": user_messages,
            "max_tokens": int(params.get("max_tokens", 256)),
            "temperature": float(params.get("temperature", 0.7)),
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        # Concatenate text contents
        text_parts = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return "".join(text_parts) or "[No content]"


class GoogleProvider(LLMProvider):
    name = "Google"

    _models: ClassVar[list[str]] = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    def list_models(self) -> list[str]:
        return self._models

    def chat(self, messages: list[dict[str, str]], model: str, params: dict[str, Any]) -> str:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return f"[Google:{model}] (dry-run) You said: {messages[-1].get('content', '')}"
        # Gemini chat
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        # Convert messages: Gemini expects role parts in a specific format
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": float(params.get("temperature", 0.7)),
                "maxOutputTokens": int(params.get("max_tokens", 256)),
            },
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "[No content]"
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)


class OllamaProvider(LLMProvider):
    name = "Ollama"

    _fallback_models: ClassVar[list[str]] = [
        "llama3.1",
        "qwen2.5",
        "phi3",
    ]

    def _base_url(self) -> str:
        # Use localhost default; allow override via env
        return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    def list_models(self) -> list[str]:
        # Try querying local Ollama for installed models
        try:
            url = f"{self._base_url()}/api/tags"
            r = requests.get(url, timeout=1.5)
            r.raise_for_status()
            data = r.json()
            models = [m.get("name", "").strip() for m in data.get("models", []) if m.get("name")]
            return models or self._fallback_models
        except Exception:
            # Silent fallback to static suggestions when service is not available
            return self._fallback_models

    def chat(self, messages: list[dict[str, str]], model: str, params: dict[str, Any]) -> str:
        url = f"{self._base_url()}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(params.get("temperature", 0.7)),
                # Ollama uses num_predict for max tokens in response
                "num_predict": int(params.get("max_tokens", 256)),
            },
        }
        try:
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            # Newer chat endpoint returns { message: { content: "..." }, ... }
            msg = data.get("message") or {}
            content = (msg.get("content") if isinstance(msg, dict) else None) or data.get("response")
            return content or "[No content]"
        except Exception:
            return f"[Ollama:{model}] (dry-run) You said: {messages[-1].get('content', '')}"


# Registry of providers
PROVIDERS: dict[str, LLMProvider] = {
    OpenAIProvider.name: OpenAIProvider(),
    AnthropicProvider.name: AnthropicProvider(),
    GoogleProvider.name: GoogleProvider(),
    OllamaProvider.name: OllamaProvider(),
}


# ----------------------------- Worker Thread -----------------------------


class LLMWorkerThread(QThread):
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, provider: LLMProvider, messages: list[dict[str, str]], model: str, params: dict[str, Any]):
        super().__init__()
        self._cancelled = False
        self.provider = provider
        self.messages = messages
        self.model = model
        self.params = params

    def cancel(self):
        self._cancelled = True
        self.progress.emit("Cancelling request...")

    def run(self):
        try:
            if self._cancelled:
                return
            self.progress.emit("Querying provider...")
            result = self.provider.chat(self.messages, self.model, self.params)
            if self._cancelled:
                return
            self.completed.emit(result)
        except Exception as e:  # pragma: no cover - network errors
            logger.exception("LLM request failed")
            self.failed.emit(str(e))


# ----------------------------- UI Factory -----------------------------


# ruff: noqa: C901
def create_llm_client_widget(style_func, scratch_pad=None):
    """Create the LLM Client widget.

    Provides provider selection, model selection (pre-populated per provider),
    chat input, parameters, and send/cancel. Integrates status styling similar
    to the HTTP Client for consistency.
    """

    # Root widget
    root = QWidget()
    root.setObjectName("llmClientRoot")
    root.setStyleSheet(get_tool_style())

    layout = QVBoxLayout(root)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    # Top bar: Provider, Model, Params, Actions
    top_bar = QHBoxLayout()

    provider_label = QLabel("Provider:")
    provider_combo = QComboBox()
    provider_combo.addItems(list(PROVIDERS.keys()))
    # Set provider from config if available; otherwise default to Ollama
    saved_provider = get_config("llm_client.provider", None)
    if isinstance(saved_provider, str):
        idx = provider_combo.findText(saved_provider)
        if idx >= 0:
            provider_combo.setCurrentIndex(idx)
    else:
        default_provider_name = "Ollama"
        default_index = provider_combo.findText(default_provider_name)
        if default_index >= 0:
            provider_combo.setCurrentIndex(default_index)

    model_label = QLabel("Model:")
    model_combo = QComboBox()

    def refresh_models():
        provider_name = provider_combo.currentText()
        models = PROVIDERS[provider_name].list_models()
        model_combo.clear()
        model_combo.addItems(models)
        # Try to select saved model if present
        saved_model = get_config("llm_client.model", None)
        if isinstance(saved_model, str):
            m_idx = model_combo.findText(saved_model)
            if m_idx >= 0:
                model_combo.setCurrentIndex(m_idx)
                return
        # If no saved model or not found, ensure a valid selection and persist it
        if model_combo.count() > 0:
            model_combo.setCurrentIndex(0)
            set_config("llm_client.model", model_combo.currentText())

    # Connect after potential initial selection so duplicates of refresh are avoided
    provider_combo.currentIndexChanged.connect(refresh_models)
    refresh_models()

    temp_label = QLabel("Temperature:")
    temp_input = QLineEdit(str(get_config("llm_client.temperature", 0.7)))
    temp_input.setFixedWidth(60)

    max_tokens_label = QLabel("Max Tokens:")
    max_tokens_input = QLineEdit(str(get_config("llm_client.max_tokens", 256)))
    max_tokens_input.setFixedWidth(80)

    send_button = QPushButton("Send")
    cancel_button = QPushButton("Cancel")
    cancel_button.setEnabled(False)

    # Optional scratch pad button (mirrors HTTP Client behavior)
    send_to_scratch_button = QPushButton("Send to Scratch Pad") if scratch_pad else None
    if send_to_scratch_button:
        # Allow the layout to shrink this button on smaller window sizes to avoid overflow
        # No fixed minimum width to keep layout responsive
        pass

    top_bar.addWidget(provider_label)
    top_bar.addWidget(provider_combo)
    top_bar.addSpacing(6)
    top_bar.addWidget(model_label)
    top_bar.addWidget(model_combo)
    top_bar.addStretch()
    top_bar.addWidget(temp_label)
    top_bar.addWidget(temp_input)
    top_bar.addSpacing(6)
    top_bar.addWidget(max_tokens_label)
    top_bar.addWidget(max_tokens_input)
    top_bar.addSpacing(12)
    top_bar.addWidget(send_button)
    top_bar.addWidget(cancel_button)
    # Moved scratch pad button to its own action row to prevent text trimming (align with HTTP Client)

    # Chat area
    chat_area = QVBoxLayout()

    system_input = QTextEdit()
    system_input.setPlaceholderText("System prompt (optional)...")
    system_input.setFixedHeight(64)

    user_input = QTextEdit()
    user_input.setPlaceholderText("Type your message and press Ctrl+Enter to send...")

    output_view = QTextEdit()
    output_view.setReadOnly(True)

    chat_area.addWidget(QLabel("System"))
    chat_area.addWidget(system_input)
    chat_area.addWidget(QLabel("User"))
    chat_area.addWidget(user_input)
    chat_area.addWidget(QLabel("Assistant"))
    chat_area.addWidget(output_view)

    # Status bar
    status_bar = QHBoxLayout()
    status_label = QLabel("Idle")
    status_label.setStyleSheet(get_status_style("idle"))
    progress = QProgressBar()
    progress.setRange(0, 0)
    progress.hide()

    status_bar.addWidget(status_label)
    status_bar.addStretch()
    status_bar.addWidget(progress)

    layout.addLayout(top_bar)
    # Action row for auxiliary buttons (keeps top bar uncluttered, like HTTP Client)
    if send_to_scratch_button:
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(send_to_scratch_button)
        layout.addLayout(action_layout)
    layout.addLayout(chat_area)
    layout.addLayout(status_bar)

    # Persist selection changes
    provider_combo.currentTextChanged.connect(lambda text: set_config("llm_client.provider", text))
    model_combo.currentTextChanged.connect(lambda text: set_config("llm_client.model", text))

    def on_temp_edit_finished():
        try:
            val = float((temp_input.text() or "").strip())
        except ValueError:
            val = float(get_config("llm_client.temperature", 0.7))
        temp_input.setText(str(val))
        set_config("llm_client.temperature", val)

    def on_max_tokens_edit_finished():
        try:
            val = int((max_tokens_input.text() or "").strip())
        except ValueError:
            val = int(get_config("llm_client.max_tokens", 256))
        max_tokens_input.setText(str(val))
        set_config("llm_client.max_tokens", val)

    temp_input.editingFinished.connect(on_temp_edit_finished)
    max_tokens_input.editingFinished.connect(on_max_tokens_edit_finished)

    # State
    worker: LLMWorkerThread | None = None
    timer = QTimer()
    timer.setInterval(300)

    def set_status(mode: str, text: str):
        status_label.setText(text)
        status_label.setStyleSheet(get_status_style(mode))

    def start_request():
        nonlocal worker
        provider = PROVIDERS[provider_combo.currentText()]
        model = model_combo.currentText()
        try:
            temperature = float(temp_input.text().strip() or 0.7)
        except ValueError:
            temperature = 0.7
        try:
            max_tokens = int(max_tokens_input.text().strip() or 256)
        except ValueError:
            max_tokens = 256

        # Persist current selections
        set_config("llm_client.provider", provider_combo.currentText())
        set_config("llm_client.model", model)
        set_config("llm_client.temperature", temperature)
        set_config("llm_client.max_tokens", max_tokens)

        messages: list[dict[str, str]] = []
        system_text = system_input.toPlainText().strip()
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": user_input.toPlainText().strip()})

        params = {"temperature": temperature, "max_tokens": max_tokens}

        # UI state changes
        set_status("running", "Sending request...")
        progress.show()
        send_button.setEnabled(False)
        cancel_button.setEnabled(True)
        output_view.clear()

        worker = LLMWorkerThread(provider, messages, model, params)

        def on_completed(text: str):
            set_status("success", "Completed")
            progress.hide()
            send_button.setEnabled(True)
            cancel_button.setEnabled(False)
            output_view.setPlainText(text)

        def on_failed(err: str):
            set_status("error", "Failed")
            progress.hide()
            send_button.setEnabled(True)
            cancel_button.setEnabled(False)
            QMessageBox.critical(root, "LLM Error", err)

        def on_progress(msg: str):
            set_status("running", msg)

        worker.completed.connect(on_completed)
        worker.failed.connect(on_failed)
        worker.progress.connect(on_progress)
        worker.start()

    def cancel_request():
        nonlocal worker
        if worker and worker.isRunning():
            worker.cancel()
            worker.quit()
            worker.wait(100)
            set_status("warning", "Cancelled")
            progress.hide()
            send_button.setEnabled(True)
            cancel_button.setEnabled(False)
            return True
        return False

    def send_to_scratch_pad_local(sp_widget, content: str):
        """Send content to the scratch pad without adding a leading separator.
        The content itself should include any trailing separator (e.g., ---)."""
        if sp_widget and content:
            current_content = sp_widget.get_content()
            new_content = f"{current_content}\n\n{content}" if current_content else content
            sp_widget.set_content(new_content)

    def send_output_to_scratch():
        if not scratch_pad:
            return
        # Collect all form data for a complete snapshot
        provider_name = provider_combo.currentText().strip()
        model_name = model_combo.currentText().strip()
        temperature_text = (temp_input.text() or "").strip()
        max_tokens_text = (max_tokens_input.text() or "").strip()
        system_text = (system_input.toPlainText() or "").strip()
        user_text = (user_input.toPlainText() or "").strip()
        answer_text = (output_view.toPlainText() or "").strip() or "[Empty assistant output]"

        # Build a formatted block and include a trailing separator
        formatted = (
            f"Provider: {provider_name}\n"
            f"Model: {model_name}\n"
            f"Temperature: {temperature_text}\n"
            f"Max Tokens: {max_tokens_text}\n\n"
            f"System:\n{(system_text if system_text else '[None]')}\n\n"
            f"Question:\n{user_text}\n\n"
            f"Answer:\n{answer_text}\n\n---"
        )
        send_to_scratch_pad_local(scratch_pad, formatted)

    send_button.clicked.connect(start_request)
    cancel_button.clicked.connect(cancel_request)
    if send_to_scratch_button:
        send_to_scratch_button.clicked.connect(send_output_to_scratch)

    # Keyboard shortcuts
    send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), root)
    send_shortcut.activated.connect(start_request)
    if os.name == "posix":  # add Cmd+Return on macOS
        send_shortcut_mac = QShortcut(QKeySequence("Meta+Return"), root)
        send_shortcut_mac.activated.connect(start_request)

    return root
