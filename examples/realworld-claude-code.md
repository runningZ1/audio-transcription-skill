# 实战案例 - Claude Code 批量视频转录

本文档记录了在 Claude Code 环境中使用音频转录 Skill 的实战经验，包括遇到的问题、解决方案和最佳实践。

## 任务背景

使用 Claude Code 调用 audio-transcription-skill，批量转录视频文件为文字，并输出格式化的 Markdown 文档。

**视频文件：**
1. `还在广撒网这套获客模_20251225165414.mp4` (31.6秒)
2. `一个行业要被团灭AI_20251225165451.mp4` (65.8秒)

## 遇到的问题

### 问题 1：环境变量在 Bash 工具中无法正确传递

**失败的尝试：**

```bash
# 尝试 1：CMD set 命令（失败）
cd "C:\Users\zijie\.claude\skills\audio-transcription-skill\scripts" && set VOLCENGINE_APP_ID=xxx && python transcribe.py --file "xxx.mp4"
# 错误：Error: Credentials required

# 尝试 2：PowerShell $env 语法（失败）
powershell -Command "$env:VOLCENGINE_APP_ID='xxx'; python transcribe.py --file 'xxx.mp4'"
# 错误：环境变量未正确传递到子进程
```

**问题原因：**
- Claude Code 的 Bash 工具执行环境与预期不同
- 环境变量在嵌套命令/shell 中传递存在问题
- 不同 shell (cmd/PowerShell) 的变量作用域差异

### 问题 2：命令行参数传递凭证的安全风险

**临时解决方案（不安全）：**

```bash
python transcribe.py --file "video.mp4" --appid "xxx" --token "xxx"
```

**安全风险：**
- Shell 历史记录会保存完整命令
- 进程列表 (`ps`) 可见命令行参数
- 日志文件可能记录敏感信息

## 最终解决方案：.env 文件配置

### 实施步骤

1. **在 Skill 目录创建 .env 文件**

```bash
# 文件位置: audio-transcription-skill/scripts/.env
VOLCENGINE_APP_ID=your_app_id
VOLCENGINE_ACCESS_TOKEN=your_access_token
```

2. **脚本自动加载 .env 文件**

脚本已更新支持从多个位置查找并加载 .env 文件：

| 位置 | 优先级 | 适用场景 |
|------|--------|----------|
| `~/.volc-asr/.env` | 最高 | 用户级配置，所有项目通用 |
| `scripts/.env` | 中 | Skill 级配置，仅此 Skill 使用 |
| `.env` (当前目录) | 最低 | 项目级配置 |

3. **直接使用，无需传递凭证**

```bash
# 现在可以直接运行，无需任何凭证参数
python scripts/transcribe.py --file "video.mp4" --text-only
```

**日志输出：**
```
2025-12-25 17:15:57,134 - INFO - Loaded 1 .env file(s)
```

## 完整工作流程

### 步骤 1：调用 Skill

```text
用户：D:\Download\video.mp4 帮我转录这个视频的文案
```

Claude Code 会自动调用 `audio-transcription-skill`。

### 步骤 2：执行转录命令

**配置好 .env 文件后，直接运行：**

```bash
python "C:\Users\zijie\.claude\skills\audio-transcription-skill\scripts\transcribe.py" \
  --file "D:\Download\video.mp4" \
  --text-only
```

脚本会自动从 `.env` 文件加载凭证。

### 步骤 3：处理输出

转录服务会自动：
1. 检测视频文件格式
2. 使用 FFmpeg 提取音轨
3. 调用火山引擎 ASR API
4. 返回转录文本

**输出示例：**

```
2025-12-25 17:00:45,515 - INFO - Detected video file: .mp4
2025-12-25 17:00:45,521 - INFO - Extracting audio from video: D:\Download\video.mp4
2025-12-25 17:00:45,789 - INFO - Audio extracted to: C:\Users\...\Temp\audio_xxx.mp3
2025-12-25 17:00:45,790 - INFO - Transcribing file: ... (0.2MB)
2025-12-25 17:00:45,790 - INFO - Sending request (ID: xxx)
2025-12-25 17:00:50,175 - INFO - Response: 20000000 - OK (LogId: xxx)
2025-12-25 17:00:50,178 - INFO - Duration: 65.8s, Text length: 434 chars

这里是转录的文字内容...
```

### 步骤 4：格式化输出

创建结构化的 Markdown 文档：

```markdown
# 视频文案转录

## 视频一：标题

**文件名：** video.mp4
**时长：** 65.8 秒
**字数：** 434 字

### 文案内容

转录的文字内容...
```

## 最佳实践

### 1. 使用 .env 文件管理凭证（推荐）

**安全且便捷的方式：**

```bash
# 用户级配置（推荐，所有项目通用）
mkdir -p ~/.volc-asr
cat > ~/.volc-asr/.env << EOF
VOLCENGINE_APP_ID=your_app_id
VOLCENGINE_ACCESS_TOKEN=your_access_token
EOF

# Windows 命令
mkdir ~/.volc-asr
# 手动创建文件并添加内容
```

**优点：**
- ✅ 安全：凭证不会出现在命令历史或进程列表中
- ✅ 便捷：配置一次，所有项目可用
- ✅ 灵活：支持多个 .env 文件位置

### 2. 批量处理多个文件

```bash
# Windows PowerShell
Get-ChildItem "D:\Download\*.mp4" | ForEach-Object {
  python scripts/transcribe.py --file $_.FullName --text-only
}

# Linux/macOS
for video in D:/Download/*.mp4; do
  python scripts/transcribe.py --file "$video" --text-only
done
```

### 3. 保存完整 JSON 结果

如果需要时间戳等详细信息：

```bash
python scripts/transcribe.py --file "video.mp4" -o result.json
```

### 4. 错误处理

常见错误及解决方法：

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `Credentials required` | API 凭证未传递 | 使用 `--appid` 和 `--token` 参数 |
| `FFmpeg not found` | 未安装 FFmpeg | `winget install ffmpeg` |
| `File not found` | 文件路径错误 | 检查路径是否正确 |
| `File too large` | 文件超过 100MB | 压缩或分割文件 |

## 实际转录结果示例

### 视频 1：获客模式宣传

**输入：** `还在广撒网这套获客模_20251225165414.mp4`
**时长：** 31.6 秒
**字数：** 196 字

> 未来三年最牛的获客方式，不是做直播，也不是短视频，不用你花钱去投广告，也不用雇人去打电话。不管你是想要全国的客户，还是想要同城的客户，通通都可以帮你搞定。帮你把真正有需求的意向客户给筛选出来，让你每天睁开眼睛，手里握的都是那种直接能沟通的精准意向客户资源。现在这种获客模式竞争很小，成本也很低。你早入局早占位，千万不要等到同行把你的客户都挖走了，你才后知后觉。聪明的老板，我带你免费体验一下。

### 视频 2：AI 营销推广

**输入：** `一个行业要被团灭AI_20251225165451.mp4`
**时长：** 65.8 秒
**字数：** 434 字

> 一个行业要被团灭了，传统营销企业正在被 AI 企业批量淘汰。为什么？因为效率差10倍，成本差20倍，根本没法竞争。
>
> 传统企业怎么做营销？雇团队做内容，雇团队拍视频，雇团队做投放，雇团队做客服，一年投入200万，线上获客3000个。
>
> AI 企业怎么做营销？一套 AI 系统做内容、拍视频、做投放、做客服，一年投入10万，线上获客55千个。
>
> （...完整内容略）

## 总结

1. **使用 .env 文件管理凭证** - 安全、便捷、无需每次传递参数
2. **推荐用户级配置** `~/.volc-asr/.env` - 配置一次，所有项目可用
3. **视频自动转音频** - 无需手动预处理
4. **`--text-only` 参数** - 适合只需要文字内容的场景
5. **批量处理** - 注意 API 调用频率限制
6. **保存完整结果** - 可获取词级时间戳等详细信息

## 凭证配置优先级

```
命令行参数 > .env 文件 > 环境变量
```

| 方式 | 安全性 | 便利性 | 推荐场景 |
|------|--------|--------|----------|
| `.env` 文件 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 日常使用（推荐）|
| 环境变量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 服务器/CI 环境 |
| 命令行参数 | ⭐ | ⭐⭐⭐⭐⭐ | 仅测试/临时覆盖 |

---

*记录日期：2025-12-25*
*更新日期：2025-12-25（添加 .env 文件支持）*
*Claude Code 版本：Latest*
*Skill 版本：audio-transcription-skill main*
