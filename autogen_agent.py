from pyautogen import AssistantAgent, UserProxyAgent

# DeepSeek coder agent
deepseek_coder = AssistantAgent(
    name="DeepSeekCoder",
    model="deepseek-ai/deepseek-coder-33b-instruct",  # Example Hugging Face model ID
    system_message=(
        "You are a coding assistant. "
        "Write clean, efficient, maintainable code. "
        "Avoid redundancy, clutter, and anti-patterns like !important in CSS. "
        "Follow best practices and keep solutions future-proof."
    ),
)

# Reviewer agent (AutoGen)
reviewer = UserProxyAgent(
    name="Reviewer",
    system_message=(
        "You are a strict code reviewer. "
        "Reject code that is redundant, cluttered, or uses !important in CSS. "
        "Ensure solutions follow DRY principles and are maintainable."
    ),
)

# Example workflow
if __name__ == "__main__":
    task = "Create a CSS rule to style a button red without breaking future overrides."
    deepseek_coder.initiate_chat(reviewer, task)
