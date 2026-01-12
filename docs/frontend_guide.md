# 前端流式对话改造指南 (支持过程可视化)

本文档描述了如何升级前端应用，以支持后端新增加的“工具调用状态”和“评估结果”可视化功能。

## 1. 协议变更说明

SSE (`/api/chat/stream`) 接口在原有基础上增加了两种新的消息类型。

### 1.1 新增消息类型

#### A. 工具开始执行 (`tool_start`)
当 AI 决定调用工具（如网络搜索）时触发。

```json
{
  "type": "tool_start",
  "tool": "serper_search",
  "input": {
    "query": "Python 2024 新特性"
  }
}
```

#### B. 工具执行完成 (`tool_result`)
当工具执行完毕并返回结果时触发。如果是搜索工具，会包含评估分数。

```json
{
  "type": "tool_result",
  "tool": "serper_search",
  "output": {
    "organic_results": [
      {
        "title": "Python 3.12 官方文档",
        "link": "https://docs.python.org/3/whatsnew/3.12.html",
        "snippet": "Python 3.12 发布于 2024 年...",
        "overall_score": 0.88,
        "relevance_score": 0.9,
        "evaluation_notes": "相关性很高；内容较新"
      }
    ]
  }
}
```

### 1.2 原有消息类型 (保持不变)

- `delta`: 文本增量
- `done`: 流结束
- `error`: 发生错误

---

## 2. 数据结构设计

建议在前端 Store 或 State 中扩展消息对象的数据结构。

```typescript
interface ToolCall {
  id: string;          // 唯一标识 (可选，可用时间戳或索引)
  tool: string;        // 工具名称，如 'serper_search'
  status: 'loading' | 'done' | 'error';
  input: any;          // 工具输入参数
  output?: any;        // 工具输出结果
}

interface Message {
  role: 'user' | 'assistant';
  content: string;     // 最终展示的文本内容
  toolCalls: ToolCall[]; // 关联的工具调用列表
}
```

---

## 3. 前端处理逻辑 (伪代码)

```javascript
// 假设这是你的 SSE 处理函数
function handleSSEMessage(eventData, currentMessage) {
  const data = JSON.parse(eventData);

  switch (data.type) {
    case 'tool_start':
      // 1. 收到工具开始信号，添加一个 loading 状态的工具调用
      currentMessage.toolCalls.push({
        tool: data.tool,
        status: 'loading',
        input: data.input,
        output: null
      });
      break;

    case 'tool_result':
      // 2. 收到工具结果，更新对应工具的状态和输出
      // 注意：这里简单取最后一个匹配的工具，实际场景可能需要 ID 匹配
      const toolCall = currentMessage.toolCalls.find(
        t => t.tool === data.tool && t.status === 'loading'
      );
      if (toolCall) {
        toolCall.status = 'done';
        toolCall.output = data.output;
      }
      break;

    case 'delta':
      // 3. 常规文本追加
      currentMessage.content += data.content;
      break;
      
    case 'done':
      console.log('Stream finished');
      break;
  }
}
```

---

## 4. UI 组件设计建议

### 4.1 搜索状态条 (Loading 态)

当 `toolCall.status === 'loading'` 时渲染。

- **样式**：建议使用轻量级的 Banner 或气泡。
- **内容**：
  - 图标：🔄 (旋转中)
  - 文本：`正在搜索网络：${toolCall.input.query}...`

### 4.2 搜索结果卡片 (Done 态)

当 `toolCall.status === 'done'` 且 `tool === 'serper_search'` 时渲染。

- **样式**：折叠面板 (Accordion)，默认可以是折叠状态，点击展开详情。
- **摘要展示**：
  - “✅ 已搜索到 ${output.organic_results.length} 条结果”
- **详情展示 (展开后)**：
  - 遍历 `output.organic_results` 渲染列表。
  - **评分徽章**：根据 `overall_score` 改变颜色。
    - Score >= 0.8: 🟢 绿色
    - Score >= 0.5: 🟡 黄色
    - Score < 0.5: 🔴 红色
  - **评估说明**：Hover 徽章时显示 `evaluation_notes` (Tooltip)。

### 4.3 示例 HTML 结构

```html
<!-- 搜索结果组件 -->
<div class="search-result-card">
  <div class="header" onclick="toggleExpand()">
    ✅ 搜索完成：找到 3 条结果
  </div>
  
  <div class="content" v-if="expanded">
    <div v-for="item in results" class="result-item">
      <div class="title-row">
        <a :href="item.link">{{ item.title }}</a>
        <span class="score-badge" :class="getScoreClass(item.overall_score)">
          {{ item.overall_score }}
        </span>
      </div>
      <div class="snippet">{{ item.snippet }}</div>
      <div class="evaluation-notes">
        💡 评估：{{ item.evaluation_notes }}
      </div>
    </div>
  </div>
</div>
```
