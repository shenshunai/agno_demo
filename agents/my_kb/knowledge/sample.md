# 示例知识文档

本文件用于演示「我的知识库」Agent 的 RAG 入库。

## 支持的文件类型

把文件放在本目录 `agents/my_kb/knowledge/` 下即可；**不限于 Markdown**。Agno 会按扩展名选择解析器，例如：

- `.md` / `.markdown` — Markdown  
- `.txt` / `.text` — 纯文本  
- `.pdf` — PDF（需已安装 `pypdf` 等依赖，本项目 requirements 已包含）  
- `.csv` — CSV  
- `.xlsx` / `.xls` — Excel  
- `.docx` / `.doc` — Word  
- `.pptx` — PowerPoint  
- `.json` — JSON  

其它扩展名一般会按**纯文本**尝试读取（具体以 Agno `ReaderFactory` 行为为准）。

## 从 URL 入库

Agno 支持 `Knowledge.insert(..., url="https://...")`，会按网页等方式拉取后再切块、嵌入。

两种方式任选：

1. **在代码里**调用：`my_kb.insert(name="某页标题", url="https://...")`  
2. **批量**：在 `agents/my_kb/` 下复制 `seed_urls.example` 为 `seed_urls.txt`，每行一个 URL（`#` 开头为注释），再运行 `load_knowledge` 脚本会自动追加这些 URL（在本地目录入库之后执行）。

注意：需能访问外网；部分站点会反爬，可能失败。

## 需要账号密码的 URL 怎么办

1. **HTTP Basic 认证（最常见）**  
   可把账号密码写进 URL（标准写法）：`https://用户名:密码@主机/路径`  
   多数 HTTP 客户端（含 Agno 用的 httpx）会按 Basic 认证发送。  
   **注意**：密码会出现在配置/日志里，生产环境更建议用下面第 2 种。

2. **Bearer / Cookie / 表单登录**  
   内置 `insert(url=...)` **不能**带头；需要自己用脚本（`httpx`/`requests`）带 `headers`/`cookies` 拉取正文，再调用：  
   `my_kb.insert(name="...", text_content="拉到的纯文本或 HTML 转文本")`  
   或先保存成文件，再用 `path=` 入库。

3. **复杂 SSO**  
   一般在应用外完成登录与导出，再把结果当文件或 `text_content` 写入知识库。


- 在项目根目录执行：`python -m agents.my_kb.scripts.load_knowledge`
- 首次或想清空重建时加参数：`python -m agents.my_kb.scripts.load_knowledge --recreate`

## 嵌入配置

向量嵌入由环境变量控制，见仓库根目录 `db/session.py` 中的 `EMBEDDING_PROVIDER` 等说明。
