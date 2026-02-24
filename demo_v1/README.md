# 申论 AI 批改可演示版本（V1）

这是一个“只接入大模型 + Prompt 评分标准”的极简演示服务。

---

## 0. 给新手先说结论（你要做的就 5 步）
1. 打开终端（Terminal）。
2. 进入项目目录：`cd /workspace/Noel`。
3. 配置 3 个环境变量（`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`）。
4. 启动服务：`python demo_v1/app.py`。
5. 浏览器打开：`http://127.0.0.1:8000/`，填内容后点击“开始批改”。

---

## 1. 运行环境
- Python 3.10+
- 无第三方依赖（标准库即可运行）

如何检查 Python 版本（在终端输入）：
```bash
python --version
```
如果显示 `Python 3.10.x` / `3.11.x` / `3.12.x` 就可以。

---

## 2. “命令到底在哪里输入？”（给初学者）
你需要在**终端（Terminal）**里输入命令，不是在 Python 文件里输入。

常见打开方式：
- macOS：打开 `Terminal`。
- Linux：打开 `Terminal`。
- Windows：打开 `PowerShell` 或 `Windows Terminal`（如果你在 WSL 里就打开 WSL 终端）。

打开终端后，先执行：
```bash
cd /workspace/Noel
```
这一步是进入项目根目录。

---

## 3. 配置环境变量（必须）
在**同一个终端窗口**输入下面三行（把 `你的key` 换成真实 key）：

```bash
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="你的key"
export LLM_MODEL="gpt-4o-mini"
```

说明：
- `LLM_BASE_URL`：模型接口地址（OpenAI 或兼容网关都行）。
- `LLM_API_KEY`：你的 API Key。
- `LLM_MODEL`：模型名。

> 注意：如果你新开了一个终端窗口，需要重新执行 `export ...`。

---

## 4. 启动服务（在终端输入）
仍然在刚才那个终端里执行：

```bash
python demo_v1/app.py
```

看到类似输出表示启动成功：

```text
Shenlun demo server running at http://0.0.0.0:8000
```

---

## 5. 打开网页并使用
1. 打开浏览器（Chrome/Edge 都行）。
2. 访问：`http://127.0.0.1:8000/`
3. 页面里填：
   - 评分标准（可保持默认“省考标准”）
   - 申论试卷
   - 参考答案
   - 考生答案
4. 点击“开始批改”。
5. 查看结果：
   - `parsed`：结构化 JSON（更适合程序处理）
   - `raw_model_output`：模型原始输出

---

## 6. 不开网页也可以（可选）
如果你想用接口测试，在终端输入：

```bash
curl -X POST "http://127.0.0.1:8000/review" \
  -H "Content-Type: application/json" \
  -d '{
    "question_paper": "题目内容...",
    "reference_answer": "参考答案...",
    "candidate_answer": "考生答案...",
    "score_standard": "省考标准"
  }'
```

健康检查：
```bash
curl "http://127.0.0.1:8000/health"
```

---

## 7. 常见报错怎么处理（新手高频）
### 报错1：`请先设置环境变量 LLM_BASE_URL、LLM_API_KEY`
原因：你还没 `export`，或者在新终端里忘了重新设置。

解决：重新执行第 3 步三条 `export` 命令。

### 报错2：浏览器打不开 `127.0.0.1:8000`
原因：服务没启动，或刚启动就被关掉了。

解决：
1) 回到终端确认 `python demo_v1/app.py` 正在运行；
2) 不要关闭这个终端窗口；
3) 再刷新浏览器。

### 报错3：调用模型失败（网络/鉴权）
原因：API Key 不对，或者网络不能访问模型网关。

解决：
- 检查 `LLM_API_KEY` 是否正确；
- 检查 `LLM_BASE_URL` 是否可用；
- 若是公司内网网关，改成你们自己的 base url。

---

## 8. 关闭服务
在运行服务的那个终端里按：
- `Ctrl + C`

即可停止服务。

---

## 9. 当前默认 Prompt
服务已内置你提供的第一版 Prompt，可通过请求体 `prompt_override` 临时覆盖。

---

## 10. 版本定位
- 该版本用于“可演示”与“快速试跑”。
- 暂未包含规则引擎、分数校准、人工复核闭环。
