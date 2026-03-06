package models

import "encoding/json"

// AnthropicRequest Anthropic /v1/messages 请求格式
type AnthropicRequest struct {
	Model       string             `json:"model" binding:"required"`
	MaxTokens   int                `json:"max_tokens" binding:"required"`
	Messages    []AnthropicMessage `json:"messages" binding:"required"`
	System      string             `json:"system,omitempty"`
	Stream      bool               `json:"stream,omitempty"`
	Temperature *float64           `json:"temperature,omitempty"`
	TopP        *float64           `json:"top_p,omitempty"`
}

// AnthropicMessage Anthropic 消息
type AnthropicMessage struct {
	Role    string      `json:"role"`
	Content interface{} `json:"content"` // string or []AnthropicContentBlock
}

// AnthropicContentBlock Anthropic 内容块
type AnthropicContentBlock struct {
	Type string `json:"type"`
	Text string `json:"text,omitempty"`
}

// GetStringContent 提取消息文本内容
func (m *AnthropicMessage) GetStringContent() string {
	if m.Content == nil {
		return ""
	}
	switch v := m.Content.(type) {
	case string:
		return v
	case []interface{}:
		var result string
		for _, item := range v {
			if block, ok := item.(map[string]interface{}); ok {
				if block["type"] == "text" {
					if text, ok := block["text"].(string); ok {
						result += text
					}
				}
			}
		}
		return result
	default:
		if data, err := json.Marshal(v); err == nil {
			return string(data)
		}
		return ""
	}
}

// ToOpenAIMessages 将 Anthropic 消息列表转换为 OpenAI 格式
func (r *AnthropicRequest) ToOpenAIMessages() []Message {
	var messages []Message
	if r.System != "" {
		messages = append(messages, Message{Role: "system", Content: r.System})
	}
	for _, m := range r.Messages {
		messages = append(messages, Message{Role: m.Role, Content: m.GetStringContent()})
	}
	return messages
}

// AnthropicResponse Anthropic 非流式响应
type AnthropicResponse struct {
	ID           string                  `json:"id"`
	Type         string                  `json:"type"`
	Role         string                  `json:"role"`
	Content      []AnthropicContentBlock `json:"content"`
	Model        string                  `json:"model"`
	StopReason   string                  `json:"stop_reason"`
	StopSequence *string                 `json:"stop_sequence"`
	Usage        AnthropicUsage          `json:"usage"`
}

// AnthropicUsage Anthropic 使用统计
type AnthropicUsage struct {
	InputTokens  int `json:"input_tokens"`
	OutputTokens int `json:"output_tokens"`
}

// ---- 流式事件类型 ----

type AnthropicStreamMessageStart struct {
	Type    string                  `json:"type"`
	Message AnthropicStreamStartMsg `json:"message"`
}

type AnthropicStreamStartMsg struct {
	ID           string        `json:"id"`
	Type         string        `json:"type"`
	Role         string        `json:"role"`
	Content      []interface{} `json:"content"`
	Model        string        `json:"model"`
	StopReason   *string       `json:"stop_reason"`
	StopSequence *string       `json:"stop_sequence"`
	Usage        AnthropicUsage `json:"usage"`
}

type AnthropicContentBlockStart struct {
	Type         string                `json:"type"`
	Index        int                   `json:"index"`
	ContentBlock AnthropicContentBlock `json:"content_block"`
}

type AnthropicContentBlockDelta struct {
	Type  string             `json:"type"`
	Index int                `json:"index"`
	Delta AnthropicTextDelta `json:"delta"`
}

type AnthropicTextDelta struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type AnthropicContentBlockStop struct {
	Type  string `json:"type"`
	Index int    `json:"index"`
}

type AnthropicMessageDelta struct {
	Type  string                    `json:"type"`
	Delta AnthropicMessageDeltaData `json:"delta"`
	Usage AnthropicUsage            `json:"usage"`
}

type AnthropicMessageDeltaData struct {
	StopReason   string  `json:"stop_reason"`
	StopSequence *string `json:"stop_sequence"`
}

type AnthropicMessageStop struct {
	Type string `json:"type"`
}

type AnthropicPing struct {
	Type string `json:"type"`
}
