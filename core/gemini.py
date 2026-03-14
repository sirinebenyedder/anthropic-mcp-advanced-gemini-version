from google import genai
from google.genai import types
import os


class GeminiMessage:
    """Mimics Anthropic's Message object so Chat/CliChat code works unchanged."""

    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason  # "end_turn" or "tool_use"


class TextBlock:
    """Mimics Anthropic's TextBlock."""

    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class ToolUseBlock:
    """Mimics Anthropic's ToolUseBlock."""

    def __init__(self, tool_id: str, name: str, input: dict):
        self.type = "tool_use"
        self.id = tool_id
        self.name = name
        self.input = input


class Gemini:
    def __init__(self, model: str):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        self.model = model

    def add_user_message(self, messages: list, message):
        """Add a user message - handles both GeminiMessage and raw content."""
        if isinstance(message, list):
            # Tool results coming back
            parts = []
            for part in message:
                if isinstance(part, dict):
                    if part.get("type") == "tool_result":
                        content = part.get("content", "")
                        if isinstance(content, list):
                            for c in content:
                                if c.get("type") == "text":
                                    parts.append(
                                        types.Part.from_function_response(
                                            name=part.get("tool_use_id", "tool"),
                                            response={"result": c.get("text", "")},
                                        )
                                    )
                        else:
                            parts.append(
                                types.Part.from_function_response(
                                    name=part.get("tool_use_id", "tool"),
                                    response={"result": str(content)},
                                )
                            )
            if parts:
                messages.append({"role": "user", "parts": parts})
        elif isinstance(message, GeminiMessage):
            messages.append({"role": "user", "parts": [types.Part.from_text(text=str(message.content))]})
        else:
            messages.append({"role": "user", "parts": [types.Part.from_text(text=str(message))]})

    def add_assistant_message(self, messages: list, message):
        """Add assistant message from GeminiMessage."""
        if isinstance(message, GeminiMessage):
            parts = []
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(types.Part.from_text(text=block.text))
                elif isinstance(block, ToolUseBlock):
                    parts.append(
                        types.Part.from_function_call(
                            name=block.name,
                            args=block.input,
                        )
                    )
            messages.append({"role": "model", "parts": parts})
        else:
            messages.append({"role": "model", "parts": [types.Part.from_text(text=str(message))]})

    def text_from_message(self, message: GeminiMessage) -> str:
        """Extract plain text from a GeminiMessage."""
        return "\n".join(
            block.text for block in message.content if isinstance(block, TextBlock)
        )

    def _convert_tools(self, tools: list) -> list:
        """Convert Anthropic-style tools to Gemini function declarations."""
        if not tools:
            return []

        declarations = []
        for tool in tools:
            schema = tool.get("input_schema", {})
            props = schema.get("properties", {})
            required = schema.get("required", [])

            parameters = {
                "type": "object",
                "properties": {
                    k: {"type": v.get("type", "string"), "description": v.get("description", "")}
                    for k, v in props.items()
                },
            }
            if required:
                parameters["required"] = required

            declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters=parameters,
                )
            )

        return [types.Tool(function_declarations=declarations)]

    def _convert_messages(self, messages: list) -> list:
        """Convert messages to Gemini format if they aren't already."""
        converted = []
        for msg in messages:
            # Already in Gemini format
            if "parts" in msg:
                converted.append(msg)
                continue

            role = "model" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "")

            if isinstance(content, str):
                converted.append({
                    "role": role,
                    "parts": [types.Part.from_text(text=content)]
                })
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append(types.Part.from_text(text=block["text"]))
                        elif block.get("type") == "tool_result":
                            result_content = block.get("content", "")
                            if isinstance(result_content, list):
                                for c in result_content:
                                    if c.get("type") == "text":
                                        parts.append(
                                            types.Part.from_function_response(
                                                name=block.get("tool_use_id", "tool"),
                                                response={"result": c["text"]},
                                            )
                                        )
                            else:
                                parts.append(
                                    types.Part.from_function_response(
                                        name=block.get("tool_use_id", "tool"),
                                        response={"result": str(result_content)},
                                    )
                                )
                if parts:
                    converted.append({"role": role, "parts": parts})

        return converted

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ) -> GeminiMessage:

        gemini_messages = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools or [])

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system or "You are a helpful assistant.",
            tools=gemini_tools if gemini_tools else None,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=gemini_messages,
            config=config,
        )

        content_blocks = []
        stop_reason = "end_turn"

        for part in response.candidates[0].content.parts:
            if part.function_call:
                stop_reason = "tool_use"
                import uuid
                content_blocks.append(
                    ToolUseBlock(
                        tool_id=str(uuid.uuid4()),
                        name=part.function_call.name,
                        input=dict(part.function_call.args),
                    )
                )
            elif part.text:
                content_blocks.append(TextBlock(text=part.text))

        return GeminiMessage(content=content_blocks, stop_reason=stop_reason)