from typing import Generator, Any, Dict
import logging

logger = logging.getLogger(__name__)


def stream_llm_response(
    client: Any, model_name: str, system_prompt: str, user_prompt_content: str
) -> Generator[Dict[str, Any], None, str]:
    """
    Shared logic to stream response from LLM.
    Yields tokens and returns full content string.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_content},
    ]

    logger.info(f"\n--- [LLM Request] Model: {model_name} ---")
    logger.info("------------------------------------------\n")

    full_content = ""

    try:
        with client.chat.completions.create(
            model=model_name, messages=messages, stream=True
        ) as response_stream:
            for chunk in response_stream:
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        token = delta.content
                        full_content += token
                        yield {"type": "token", "content": token}
    except GeneratorExit:
        # Stream closed by caller (e.g. user abort or response closed); treat as normal.
        logger.info("[LLM Stream] Closed by caller.")
        return full_content

    return full_content
