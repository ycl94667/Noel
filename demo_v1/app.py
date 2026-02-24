import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

DEFAULT_PROMPT = """你是一位资深的公务员考试阅卷老师，熟练掌握申论答题模板思路，给分点扣分点。请根据上面申论考试的试卷及参考答案，结合答题思路来对我的答案进行踩点给分。要求给出得、扣分理由，提出改正建议，并在原有的答案文本上比对参考答案进行勾划。 (答题最好是问题一二三分清楚，用省考标准打分、给出详细得分点、再归纳错误、改正方法和思路、再帮根据这几份答案帮我优化出一篇满分答案。把答案精简为加上字符，按答题卡的格式，控制在要求字数之内。)对参考答案进行打分，并罗列出参考答案的优先级。"""

JSON_SCHEMA_HINT = """
请仅返回 JSON，字段如下：
{
  "total_score": number,
  "sub_scores": [
    {
      "dimension": "string",
      "score": number,
      "max_score": number,
      "gain_reasons": ["string"],
      "deduction_reasons": ["string"]
    }
  ],
  "answer_markup": "在考生原答案上做【得分点】、【缺失点】标记后的文本",
  "mistakes_summary": ["string"],
  "improvement_suggestions": ["string"],
  "optimized_full_score_answer": "按答题卡格式给出的优化答案",
  "reference_answer_scoring": {
    "score": number,
    "priority_points": [
      {"point": "string", "priority": "高|中|低", "reason": "string"}
    ]
  }
}
"""


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)




def serve_index(handler: BaseHTTPRequestHandler) -> bool:
    if handler.path != '/':
        return False
    index_path = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
    try:
        with open(index_path, 'rb') as f:
            body = f.read()
    except OSError:
        _json_response(handler, 500, {'error': 'index file not found'})
        return True

    handler.send_response(200)
    handler.send_header('Content-Type', 'text/html; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
    return True

def call_llm(user_content: str) -> str:
    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not base_url or not api_key:
        raise RuntimeError("请先设置环境变量 LLM_BASE_URL、LLM_API_KEY")

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "你是申论智能批改助手，必须严格按用户要求评分并返回结构化结果。"},
            {"role": "user", "content": user_content},
        ],
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"调用LLM失败: {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"LLM返回格式异常: {data}") from exc


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        marker = "```json"
        if marker in text:
            part = text.split(marker, 1)[1].split("```", 1)[0].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                return None
        return None


def build_user_content(payload: Dict[str, Any]) -> str:
    prompt = payload.get("prompt_override") or DEFAULT_PROMPT
    return f"""
{prompt}

评分标准：{payload.get('score_standard', '省考标准')}

【申论试卷】
{payload.get('question_paper', '')}

【参考答案】
{payload.get('reference_answer', '')}

【考生答案】
{payload.get('candidate_answer', '')}

{JSON_SCHEMA_HINT}
""".strip()


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if serve_index(self):
            return
        if self.path == "/health":
            _json_response(self, 200, {"status": "ok"})
        else:
            _json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/review":
            _json_response(self, 404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)
        except Exception:
            _json_response(self, 400, {"error": "invalid json body"})
            return

        required = ["question_paper", "reference_answer", "candidate_answer"]
        missing = [k for k in required if not payload.get(k)]
        if missing:
            _json_response(self, 400, {"error": f"missing required fields: {', '.join(missing)}"})
            return

        user_content = build_user_content(payload)
        try:
            model_output = call_llm(user_content)
        except RuntimeError as exc:
            _json_response(self, 502, {"error": str(exc)})
            return

        _json_response(
            self,
            200,
            {
                "raw_model_output": model_output,
                "parsed": try_parse_json(model_output),
            },
        )


def run() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), DemoHandler)
    print(f"Shenlun demo server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
