# W6 双引擎封装：本地 Ollama + 云端 DeepSeek 统一接口
# 依赖：pip install openai requests python-dotenv
# 课后增强：打印每次调用的耗时、token 和估算费用，便于判断任务该走本地还是云端。
import os
import sys
import time

# 把代码包根目录加入 sys.path，保证跨周导入 weekpath。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import weekpath  # noqa: E402

weekpath.load_env()

import requests  # noqa: E402
import openai  # noqa: E402


def _log(message):
    """把运行时统计写到 stderr，保持 ask() 的返回答案干净。"""
    print(message, file=sys.stderr)


class LocalEngine:
    """本地引擎：requests 直连 Ollama，适合隐私、离线和低频固定任务。"""

    def __init__(self, model=None, base_url=None, timeout=60):
        self.model = model or os.getenv("LOCAL_MODEL", "qwen2.5:0.5b")
        raw_url = base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        if "://" not in raw_url:
            raw_url = "http://" + raw_url
        self.base_url = raw_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        # 防止系统代理接管 localhost 请求。
        self.session.trust_env = False

    def ask(self, prompt, history=None, temperature=0.7, max_tokens=800):
        messages = list(history or [])
        messages.append({"role": "user", "content": prompt})
        start = time.perf_counter()
        response = self.session.post(
            self.base_url + "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        elapsed = time.perf_counter() - start
        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")
        eval_duration = data.get("eval_duration") or 0
        speed = (
            completion_tokens / (eval_duration / 1e9)
            if eval_duration and completion_tokens
            else None
        )
        _log(
            "[local] %.2fs | prompt_tokens=%s | completion_tokens=%s | %.1f tok/s"
            % (elapsed, prompt_tokens, completion_tokens, speed or 0)
        )
        return data["message"]["content"]


class APIEngine:
    """云端引擎：DeepSeek OpenAI 兼容接口，客户端按需创建。"""

    def __init__(self, base_url=None, model=None, timeout=30):
        self.base_url = base_url or os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
        )
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        """只有真正调用云端时才创建客户端，缺密钥时纯本地模式仍能运行。"""
        if self._client is None:
            key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
            if not key or key.startswith("your_"):
                raise RuntimeError(
                    "未配置 DEEPSEEK_API_KEY；可先使用 prefer='local'。"
                )
            self._client = openai.OpenAI(
                base_url=self.base_url,
                api_key=key,
                timeout=self.timeout,
            )
        return self._client

    def _estimate_cost(self, prompt_tokens, completion_tokens):
        """单价从环境变量读取；没有配置时只显示 token，不猜价格。"""
        input_price = (os.getenv("DEEPSEEK_INPUT_PRICE_PER_MILLION") or "").strip()
        output_price = (os.getenv("DEEPSEEK_OUTPUT_PRICE_PER_MILLION") or "").strip()
        if not input_price or not output_price:
            return None
        try:
            return (
                (prompt_tokens or 0) * float(input_price)
                + (completion_tokens or 0) * float(output_price)
            ) / 1_000_000
        except ValueError:
            return None

    def ask(self, prompt, history=None, temperature=0.7, max_tokens=800):
        messages = list(history or [])
        messages.append({"role": "user", "content": prompt})
        start = time.perf_counter()
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = time.perf_counter() - start
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        cost = self._estimate_cost(prompt_tokens, completion_tokens)
        cost_text = "cost=$%.6f" % cost if cost is not None else "cost=未配置单价"
        _log(
            "[api] %.2fs | prompt_tokens=%s | completion_tokens=%s | total_tokens=%s | %s"
            % (elapsed, prompt_tokens, completion_tokens, total_tokens, cost_text)
        )
        return response.choices[0].message.content


class LLM:
    """统一入口：ask(prompt, prefer='local'/'api')，失败时双向自动回退。"""

    def __init__(self, local_model=None):
        self.local = LocalEngine(local_model)
        self.api = APIEngine()

    def ask(self, prompt, prefer="local", history=None, **kwargs):
        if prefer not in ("local", "api"):
            raise ValueError("prefer 只能是 'local' 或 'api'")
        if prefer == "local":
            first, second, tag = self.local, self.api, "本地失败，自动切换云端"
        else:
            first, second, tag = self.api, self.local, "云端失败，自动切换本地"
        try:
            return first.ask(prompt, history=history, **kwargs)
        except Exception as exc:
            # 不允许静默失败：打印原始异常，再尝试另一侧引擎。
            _log("[%s] %s: %s" % (tag, type(exc).__name__, exc))
            return second.ask(prompt, history=history, **kwargs)


if __name__ == "__main__":
    question = "给《愚公移山》出一道 HSK4 阅读理解题"
    prefer = os.getenv("PREFER", "local")
    print(LLM().ask(question, prefer=prefer))